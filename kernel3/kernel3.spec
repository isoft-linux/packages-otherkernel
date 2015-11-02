#NOTE: we do not provide debuginfo/kernel-tools for non-main kernel

%define debug_package %{nil}

%define kversion 3.18.23
%define release 74

%define extraversion -%{release}

%define KVERREL %{version}-%{release}

%define hdrarch %_target_cpu
%define asmarch %_target_cpu

%ifarch x86_64
%define asmarch x86
%endif

Name: kernel3
Summary: The Linux kernel (the core of the Linux operating system)
License: GPLv2
Version: %{kversion}
Release: %{release}
ExclusiveArch: noarch x86_64
ExclusiveOS: Linux
Provides: kernel3-drm = 4.3.0
Provides: kernel3-%{_target_cpu} = %{kversion}-%{release}
Requires(pre): kmod, grub, dracut 
# We can't let RPM do the dependencies automatic because it'll then pick up
# a correct but undesirable perl dependency from the module headers which
# isn't required for the kernel proper to function
AutoReq: no
AutoProv: yes

#
# List the packages used during the kernel build
#
BuildRequires: kmod, patch >= 2.5.4, bash >= 2.03
BuildRequires: bzip2, busybox, m4, perl, make >= 3.78
BuildRequires: gcc >= 3.4.2, binutils >= 2.12
BuildRequires: bc

Source0: linux-%{kversion}.tar.xz

Source20: kernel-%{kversion}-x86_64.config

Patch0: linux-tune-cdrom-default.patch
Patch1: linux-3.14-fix-suspend.patch
Patch2: thinkpad_acpi_support_new_bios_version_string.patch
Patch3: backport-synaptics-from-kernel-4.2.patch


Patch450: input-kill-stupid-messages.patch
Patch452: no-pcspkr-modalias.patch

Patch470: die-floppy-die.patch


BuildRoot: %{_tmppath}/kernel-%{KVERREL}-root-%{_target_cpu}


%description
The kernel package contains the Linux kernel (vmlinuz), the core of any
Linux operating system.  The kernel handles the basic functions
of the operating system:  memory allocation, process allocation, device
input and output, etc.

%package devel
Summary: Development package for building kernel modules to match the kernel.
AutoReqProv: no
Provides: kernel3-devel-%{_target_cpu} = %{kversion}-%{release}
Requires(pre): /usr/bin/find

%description devel
This package provides kernel headers and makefiles sufficient to build modules
against the kernel package.


%package headers
Summary: Header files for the Linux kernel for use by glibc

%description headers
Kernel-headers includes the C header files that specify the interface
between the Linux kernel and userspace libraries and programs.  The
header files define structures and constants that are needed for
building most standard programs and are also needed for rebuilding the
glibc package.


%prep
if [ ! -d %{name}-%{kversion}/vanilla ]; then
%setup -q -n %{name}-%{version} -c
  mv linux-%{kversion} vanilla
else
  cd %{name}-%{kversion}
  if [ -d linux-%{kversion}.%{_target_cpu} ]; then
     rm -rf deleteme.%{_target_cpu}
     mv linux-%{kversion}.%{_target_cpu} deleteme.%{_target_cpu}
     rm -rf deleteme.%{_target_cpu} &
  fi
fi

cp -rl vanilla linux-%{kversion}.%{_target_cpu}

cd linux-%{kversion}.%{_target_cpu}

%patch0 -p1
%patch1 -p1
%patch2 -p1
%patch3 -p1

%patch450 -p1
%patch452 -p1
%patch470 -p1

# END OF PATCH APPLICATIONS


# get rid of unwanted files resulting from patch fuzz
find . \( -name "*.orig" -o -name "*~" \) -exec rm -f {} \; >/dev/null

cd ..


%build
pushd linux-%{kversion}.%{_target_cpu}

echo BUILDING A KERNEL FOR %{_target_cpu}...

make -s mrproper

#copy config file.
cp %{SOURCE20} .config

sed -i -e "s/^EXTRAVERSION.*/EXTRAVERSION = %{extraversion}/" Makefile

make -s ARCH=%_target_cpu oldnoconfig > /dev/null
make -s ARCH=%_target_cpu %{?_smp_mflags} bzImage 
make -s ARCH=%_target_cpu %{?_smp_mflags} modules || exit 1
popd


%install
rm -rf $RPM_BUILD_ROOT

# Start installing the results
pushd linux-%{kversion}.%{_target_cpu}

#kernel Image and related files.
mkdir -p $RPM_BUILD_ROOT/boot
install -m 644 .config $RPM_BUILD_ROOT/boot/config-%{KVERREL}
install -m 644 System.map $RPM_BUILD_ROOT/boot/System.map-%{KVERREL}
touch $RPM_BUILD_ROOT/boot/initrd-%{KVERREL}.img
cp arch/%{asmarch}/boot/bzImage $RPM_BUILD_ROOT/boot/vmlinuz-%{KVERREL}

if [ -f arch/%{asmarch}/boot/zImage.stub ]; then
  cp arch/%{asmarch}/boot/zImage.stub $RPM_BUILD_ROOT/boot/zImage.stub-%{KVERREL} || :
fi

#Modules
mkdir -p $RPM_BUILD_ROOT/lib/modules/%{KVERREL}
make -s ARCH=%_target_cpu INSTALL_MOD_PATH=$RPM_BUILD_ROOT modules_install KERNELRELEASE=%{KVERREL}


#Devel
rm -f $RPM_BUILD_ROOT/lib/modules/%{KVERREL}/build
rm -f $RPM_BUILD_ROOT/lib/modules/%{KVERREL}/source
mkdir -p $RPM_BUILD_ROOT/lib/modules/%{KVERREL}/build
(cd $RPM_BUILD_ROOT/lib/modules/%{KVERREL} ; ln -s build source)

# first copy everything
cp --parents `find  -type f -name "Makefile*" -o -name "Kconfig*"` $RPM_BUILD_ROOT/lib/modules/%{KVERREL}/build
cp Module.symvers $RPM_BUILD_ROOT/lib/modules/%{KVERREL}/build


# then drop all but the needed Makefiles/Kconfig files
rm -rf $RPM_BUILD_ROOT/lib/modules/%{KVERREL}/build/Documentation
rm -rf $RPM_BUILD_ROOT/lib/modules/%{KVERREL}/build/scripts
rm -rf $RPM_BUILD_ROOT/lib/modules/%{KVERREL}/build/include
cp .config $RPM_BUILD_ROOT/lib/modules/%{KVERREL}/build
cp -a scripts $RPM_BUILD_ROOT/lib/modules/%{KVERREL}/build
if [ -d arch/%{asmarch}/scripts ]; then
  cp -a arch/%{asmarch}/scripts $RPM_BUILD_ROOT/lib/modules/%{KVERREL}/build/arch/%{asmarch} || :
fi
if [ -f arch/%{asmarch}/*lds ]; then
  cp -a arch/%{asmarch}/*lds $RPM_BUILD_ROOT/lib/modules/%{KVERREL}/build/arch/%{asmarch}/ || :
fi
rm -f $RPM_BUILD_ROOT/lib/modules/%{KVERREL}/build/scripts/*.o
rm -f $RPM_BUILD_ROOT/lib/modules/%{KVERREL}/build/scripts/*/*.o
if [ -d arch/%{asmarch}/include ]; then
  cp -a --parents arch/%{asmarch}/include $RPM_BUILD_ROOT/lib/modules/%{KVERREL}/build/
fi

mkdir -p $RPM_BUILD_ROOT/lib/modules/%{KVERREL}/build/include
pushd include
cp -a uapi xen acpi config crypto keys linux math-emu media net pcmcia rdma rxrpc scsi sound trace video asm-generic $RPM_BUILD_ROOT/lib/modules/%{KVERREL}/build/include
asmdir="../arch/%{asmarch}/include/asm"
cp -a $asmdir $RPM_BUILD_ROOT/lib/modules/%{KVERREL}/build/include/
ln -s asm-$Arch $RPM_BUILD_ROOT/lib/modules/%{KVERREL}/build/include/asm
# generated/*.h is necessary
# generated/uapi/linux/version.h is necessary
mkdir -p $RPM_BUILD_ROOT/lib/modules/%{KVERREL}/build/include/generated/
install -m644 ./generated/*.h $RPM_BUILD_ROOT/lib/modules/%{KVERREL}/build/include/generated/
install -m644 ./generated/uapi/linux/version.h $RPM_BUILD_ROOT/lib/modules/%{KVERREL}/build/include/generated/
popd

pushd $RPM_BUILD_ROOT/lib/modules/%{KVERREL}/build/include/linux/
ln -fs ../generated/*.h .
popd

# Make sure the Makefile and version.h have a matching timestamp so that
# external modules can be built
touch -r $RPM_BUILD_ROOT/lib/modules/%{KVERREL}/build/Makefile $RPM_BUILD_ROOT/lib/modules/%{KVERREL}/build/include/linux/version.h
touch -r $RPM_BUILD_ROOT/lib/modules/%{KVERREL}/build/.config $RPM_BUILD_ROOT/lib/modules/%{KVERREL}/build/include/linux/autoconf.h

# Copy .config to include/config/auto.conf so "make prepare" is unnecessary.
cp $RPM_BUILD_ROOT/lib/modules/%{KVERREL}/build/.config $RPM_BUILD_ROOT/lib/modules/%{KVERREL}/build/include/config/auto.conf


# Install kernel headers
make ARCH=%{hdrarch} INSTALL_HDR_PATH=$RPM_BUILD_ROOT/usr headers_install
# remove drm headers, libdrm-2.4.1 is OK.
rm -rf $RPM_BUILD_ROOT/usr/include/drm

# dirs for additional modules per module-init-tools, kbuild/modules.txt
mkdir -p $RPM_BUILD_ROOT/lib/modules/%{KVERREL}/extra
mkdir -p $RPM_BUILD_ROOT/lib/modules/%{KVERREL}/updates
mkdir -p $RPM_BUILD_ROOT/lib/modules/%{KVERREL}/weak-updates

#fix modules perms.
find $RPM_BUILD_ROOT/lib/modules/%{KVERREL} -name "*.ko" -type f >modnames

# mark modules executable so that strip-to-file can strip them
cat modnames | xargs chmod u+x
popd

# Strip modules...
pushd $RPM_BUILD_ROOT/lib/modules
find . -name "*.ko" |xargs strip -R .comment --strip-unneeded
popd

#not main kernel, remove kernel-headers
rm -rf %{buildroot}%{_includedir}

#not main kernel, even do not own /lib/firmware
#/lib/firmware is owned by main kernel.
#All firmwares provided by linux-firmware and other firmware packages.
rm -rf %{buildroot}/lib/firmware

%clean
rm -rf $RPM_BUILD_ROOT

###
### scripts
###

%post
depmod -a %{KVERREL} >/dev/null ||:
dracut -f /boot/initrd-%{KVERREL}.img %{KVERREL} >/dev/null ||:
#mkinitcpio -g /boot/initrd-%{kversion}-%{release}.img -k %{kversion}-%{release}||:
grub-mkconfig -o /boot/grub/grub.cfg >/dev/null ||:

%postun
grub-mkconfig -o /boot/grub/grub.cfg >/dev/null ||:

%preun


%files
%defattr(-,root,root)
/boot/vmlinuz-%{KVERREL}
/boot/System.map-%{KVERREL}
/boot/config-%{KVERREL}
%dir /lib/modules/%{KVERREL}
/lib/modules/%{KVERREL}/modules.order
/lib/modules/%{KVERREL}/modules.builtin
/lib/modules/%{KVERREL}/kernel
/lib/modules/%{KVERREL}/extra
/lib/modules/%{KVERREL}/updates
/lib/modules/%{KVERREL}/weak-updates
%exclude /lib/modules/%{KVERREL}/build
%exclude /lib/modules/%{KVERREL}/source
%ghost /boot/initrd-%{KVERREL}.img
%ghost /lib/modules/%{KVERREL}/modules.alias
%ghost /lib/modules/%{KVERREL}/modules.alias.bin
%ghost /lib/modules/%{KVERREL}/modules.builtin.bin
%ghost /lib/modules/%{KVERREL}/modules.dep
%ghost /lib/modules/%{KVERREL}/modules.dep.bin
%ghost /lib/modules/%{KVERREL}/modules.devname
%ghost /lib/modules/%{KVERREL}/modules.softdep
%ghost /lib/modules/%{KVERREL}/modules.symbols
%ghost /lib/modules/%{KVERREL}/modules.symbols.bin


%files devel
%defattr(-,root,root)
%verify(not mtime) /lib/modules/%{KVERREL}/build
%verify(not mtime) /lib/modules/%{KVERREL}/source


#%files headers
#%defattr(-,root,root)
#/usr/include/*


%changelog
* Fri Sep 04 2015 Cjacker <cjacker@foxmail.com>
- update to 3.18.21

* Sun Aug 16 2015 Cjacker <cjacker@foxmail.com>
- rename to kernel3 to co-exist with kernel package.
- add patch2 to fix thinkpad_acpi with x250.
- add patch3, backport synaptics from kernel-4.2
