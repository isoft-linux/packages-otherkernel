%define kversion 4.2.3
%define release 96

%define extraversion -%{release}

%define KVERREL %{version}-%{release}

%define hdrarch %_target_cpu
%define asmarch %_target_cpu

%ifarch x86_64
%define asmarch x86
%endif

# Architectures we build tools/cpupower on
%define cpupowerarchs %{ix86} x86_64

Name: kernel42
Summary: The Linux kernel (the core of the Linux operating system)
License: GPLv2
Version: %{kversion}
Release: %{release}
ExclusiveArch: noarch x86_64
ExclusiveOS: Linux
Provides: kernel-drm = 4.3.0
Provides: kernel-%{_target_cpu} = %{kversion}-%{release}
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

#for kernel tools
BuildRequires: pciutils-devel gettext ncurses-devel

Source0: linux-%{kversion}.tar.xz

Source20: kernel-%{kversion}-x86_64.config

# Sources for kernel-tools
Source2000: cpupower.service
Source2001: cpupower.config

Patch0: linux-tune-cdrom-default.patch

Patch450: input-kill-stupid-messages.patch
Patch452: no-pcspkr-modalias.patch

Patch470: die-floppy-die.patch

Patch500: kdbus.patch

Patch601: amd-xgbe-a0-Add-support-for-XGBE-on-A0.patch
Patch602: amd-xgbe-phy-a0-Add-support-for-XGBE-PHY-on-A0.patch
Patch603: ath9k-rx-dma-stop-check.patch
Patch604: disable-i8042-check-on-apple-mac.patch
Patch605: drm-i915-hush-check-crtc-state.patch
Patch606: drm-i915-turn-off-wc-mmaps.patch
Patch607: HID-chicony-Add-support-for-Acer-Aspire-Switch-12.patch
Patch608: Input-synaptics-pin-3-touches-when-the-firmware-repo.patch
Patch609: scsi-sd_revalidate_disk-prevent-NULL-ptr-deref.patch
Patch610: usb-make-xhci-platform-driver-use-64-bit-or-32-bit-D.patch
Patch611: watchdog-Disable-watchdog-on-virtual-machines.patch
Patch612: xen-pciback-Don-t-disable-PCI_COMMAND-on-PCI-device-.patch
Patch613: ideapad-laptop-Add-Lenovo-Yoga-3-14-to-no_hw_rfkill-.patch

BuildRoot: %{_tmppath}/kernel42-%{KVERREL}-root-%{_target_cpu}


%description
The kernel package contains the Linux kernel (vmlinuz), the core of any
Linux operating system.  The kernel handles the basic functions
of the operating system:  memory allocation, process allocation, device
input and output, etc.

%package devel
Summary: Development package for building kernel modules to match the kernel.
AutoReqProv: no
Provides: kernel-devel-%{_target_cpu} = %{kversion}-%{release}
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

%package -n kernel-tools
Summary: Assortment of tools for the Linux kernel
License: GPLv2
Provides:  cpupowerutils = 1:009-0.6.p1
Obsoletes: cpupowerutils < 1:009-0.6.p1
Provides:  cpufreq-utils = 1:009-0.6.p1
Provides:  cpufrequtils = 1:009-0.6.p1
Obsoletes: cpufreq-utils < 1:009-0.6.p1
Obsoletes: cpufrequtils < 1:009-0.6.p1
Obsoletes: cpuspeed < 1:1.5-16
Requires: kernel-tools-libs = %{version}-%{release}
%description -n kernel-tools
This package contains the tools/ directory from the kernel source
and the supporting documentation.

%package -n kernel-tools-libs
Summary: Libraries for the kernels-tools
License: GPLv2
%description -n kernel-tools-libs
This package contains the libraries built from the tools/ directory
from the kernel source.

%package -n kernel-tools-libs-devel
Summary: Assortment of tools for the Linux kernel
License: GPLv2
Requires: kernel-tools = %{version}-%{release}
Provides:  cpupowerutils-devel = 1:009-0.6.p1
Obsoletes: cpupowerutils-devel < 1:009-0.6.p1
Requires: kernel-tools-libs = %{version}-%{release}
Provides: kernel-tools-devel
%description -n kernel-tools-libs-devel
This package contains the development files for the tools/ directory from
the kernel source.


%prep
if [ ! -d kernel42-%{kversion}/vanilla ]; then
%setup -q -n %{name}-%{version} -c
  mv linux-%{kversion} vanilla
else
  cd kernel42-%{kversion}
  if [ -d linux-%{kversion}.%{_target_cpu} ]; then
     rm -rf deleteme.%{_target_cpu}
     mv linux-%{kversion}.%{_target_cpu} deleteme.%{_target_cpu}
     rm -rf deleteme.%{_target_cpu} &
  fi
fi

cp -rl vanilla linux-%{kversion}.%{_target_cpu}

cd linux-%{kversion}.%{_target_cpu}

%patch0 -p1

%patch450 -p1
%patch452 -p1
%patch470 -p1
%patch500 -p1

%patch601 -p1
%patch602 -p1
%patch603 -p1
%patch604 -p1
%patch605 -p1
%patch606 -p1
%patch607 -p1
%patch608 -p1
%patch609 -p1
%patch610 -p1
%patch611 -p1
%patch612 -p1
%patch613 -p1

# END OF PATCH APPLICATIONS


# get rid of unwanted files resulting from patch fuzz
find . \( -name "*.orig" -o -name "*~" \) -exec rm -f {} \; >/dev/null

cd ..


%build
pushd linux-%{kversion}.%{_target_cpu}

#build kernel
echo BUILDING A KERNEL FOR %{_target_cpu}...

make -s mrproper

#copy config file.
cp %{SOURCE20} .config

sed -i -e "s/^EXTRAVERSION.*/EXTRAVERSION = %{extraversion}/" Makefile

make -s ARCH=%_target_cpu oldnoconfig > /dev/null
make -s ARCH=%_target_cpu %{?_smp_mflags} bzImage 
make -s ARCH=%_target_cpu %{?_smp_mflags} modules || exit 1

##build kernel tools
#%ifarch %{cpupowerarchs}
## cpupower
## make sure version-gen.sh is executable.
#chmod +x tools/power/cpupower/utils/version-gen.sh
#make %{?_smp_mflags} -C tools/power/cpupower CPUFREQ_BENCH=false
#%ifarch %{ix86}
#    pushd tools/power/cpupower/debug/i386
#    make %{?_smp_mflags} centrino-decode powernow-k8-decode
#    popd
#%endif
#%ifarch x86_64
#    pushd tools/power/cpupower/debug/x86_64
#    make %{?_smp_mflags} centrino-decode powernow-k8-decode
#    popd
#%endif
#%ifarch %{ix86} x86_64
#   pushd tools/power/x86/x86_energy_perf_policy/
#   make
#   popd
#   pushd tools/power/x86/turbostat
#   make
#   popd
#%endif #turbostat/x86_energy_perf_policy
#%endif
#pushd tools/thermal/tmon/
#make
#popd


popd #linux-%{kversion}.%{_target_cpu}


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

#install kernel tools
#%ifarch %{cpupowerarchs}
#make -C tools/power/cpupower DESTDIR=$RPM_BUILD_ROOT libdir=%{_libdir} mandir=%{_mandir} CPUFREQ_BENCH=false install
#rm -f %{buildroot}%{_libdir}/*.{a,la}
#%find_lang cpupower
#mv cpupower.lang ../
#%ifarch %{ix86}
#    pushd tools/power/cpupower/debug/i386
#    install -m755 centrino-decode %{buildroot}%{_bindir}/centrino-decode
#    install -m755 powernow-k8-decode %{buildroot}%{_bindir}/powernow-k8-decode
#    popd
#%endif
#%ifarch x86_64
#    pushd tools/power/cpupower/debug/x86_64
#    install -m755 centrino-decode %{buildroot}%{_bindir}/centrino-decode
#    install -m755 powernow-k8-decode %{buildroot}%{_bindir}/powernow-k8-decode
#    popd
#%endif
#chmod 0755 %{buildroot}%{_libdir}/libcpupower.so*
#mkdir -p %{buildroot}%{_unitdir} %{buildroot}%{_sysconfdir}/sysconfig
#install -m644 %{SOURCE2000} %{buildroot}%{_unitdir}/cpupower.service
#install -m644 %{SOURCE2001} %{buildroot}%{_sysconfdir}/sysconfig/cpupower
#%endif
#%ifarch %{ix86} x86_64
#   mkdir -p %{buildroot}%{_mandir}/man8
#   pushd tools/power/x86/x86_energy_perf_policy
#   make DESTDIR=%{buildroot} install
#   popd
#   pushd tools/power/x86/turbostat
#   make DESTDIR=%{buildroot} install
#   popd
#%endif #turbostat/x86_energy_perf_policy
#pushd tools/thermal/tmon
#make INSTALL_ROOT=%{buildroot} install
#popd 
#end install kernel tools
popd

# Strip modules...
pushd $RPM_BUILD_ROOT/lib/modules
find . -name "*.ko" |xargs strip -R .comment --strip-unneeded
popd


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

%post -n kernel-tools -p /sbin/ldconfig

%postun -n kernel-tools -p /sbin/ldconfig


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
/lib/firmware

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
#
#%files -n kernel-tools -f cpupower.lang
#%defattr(-,root,root)
#%ifarch %{cpupowerarchs}
#%{_bindir}/cpupower
#%ifarch %{ix86} x86_64
#%{_bindir}/centrino-decode
#%{_bindir}/powernow-k8-decode
#%endif
#%{_unitdir}/cpupower.service
#%{_mandir}/man[1-8]/cpupower*
#%config(noreplace) %{_sysconfdir}/sysconfig/cpupower
#%ifarch %{ix86} x86_64
#%{_bindir}/x86_energy_perf_policy
#%{_mandir}/man8/x86_energy_perf_policy*
#%{_bindir}/turbostat
#%{_mandir}/man8/turbostat*
#%endif
#%{_bindir}/tmon
#%endif
#
#%ifarch %{cpupowerarchs}
#%files -n kernel-tools-libs
#%{_libdir}/libcpupower.so.0
#%{_libdir}/libcpupower.so.0.0.0
#
#%files -n kernel-tools-libs-devel
#%{_libdir}/libcpupower.so
#%{_includedir}/cpufreq.h
#%endif


%changelog
* Wed Sep 30 2015 Cjacker <cjacker@foxmail.com>
- update to kernel42-4.2.2

* Wed Sep 23 2015 Cjacker <cjacker@foxmail.com>
- update to kernel-4.2.1, rename to kernel42

* Tue Aug 25 2015 Cjacker <cjacker@foxmail.com>
- tune kernel config file. hope to fix usb issue from Yetist.

* Mon Aug 24 2015 Cjacker <cjacker@foxmail.com>
- update to 4.2.0rc8
- remove patch614 dell sound noise fix, already upstream.

* Wed Aug 19 2015 Cjacker <cjacker@foxmail.com>
- build kernel-tools package.

* Mon Aug 17 2015 Cjacker <cjacker@foxmail.com>
- update to 4.2rc7
- enable intel prelimitary support in drm.
- remove Group from spec

* Sat Aug 15 2015 Cjacker <cjacker@foxmail.com>
- update to 4.2rc6
- disable AMDGPU_CIK currently, radeon driver provide better support.
 
* Mon Aug 03 2015 Cjacker <cjacker@foxmail.com>
- update to 4.2-rc5

* Sun Aug 02 2015 Cjacker <cjacker@foxmail.com>
- enable smack LSM
- add kdbus

* Mon Jul 20 2015 Cjacker <cjacker@foxmail.com>
- update to rc3
