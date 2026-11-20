#!/usr/bin/env python3
"""Prepare media for the dedicated blank Nextgen Windows QA VM only."""
from pathlib import Path
import secrets,json,html,shutil,subprocess,argparse,hashlib
parser=argparse.ArgumentParser();parser.add_argument("--bootstrap",action="store_true");args=parser.parse_args()
root=Path(__file__).resolve().parents[2];work=root/'artifacts/windows-vm';seed=work/'seed';seed.mkdir(parents=True,exist_ok=True)
credentials=work/'credentials.json'
if credentials.exists():password=json.loads(credentials.read_text())['password']
else:
 password=secrets.token_urlsafe(24)+'aA1!';credentials.write_text(json.dumps({'username':'NextgenQA','password':password},indent=2));credentials.chmod(0o600)
header='name="{name}" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS"'
def component(name,body):return '<component '+header.format(name=name)+'>'+body+'</component>'
locale='<InputLocale>en-US</InputLocale><SystemLocale>en-US</SystemLocale><UILanguage>en-US</UILanguage><UserLocale>en-US</UserLocale>'
setup='''<DiskConfiguration><Disk wcm:action="add"><DiskID>0</DiskID><WillWipeDisk>true</WillWipeDisk><CreatePartitions><CreatePartition wcm:action="add"><Order>1</Order><Type>EFI</Type><Size>260</Size></CreatePartition><CreatePartition wcm:action="add"><Order>2</Order><Type>MSR</Type><Size>16</Size></CreatePartition><CreatePartition wcm:action="add"><Order>3</Order><Type>Primary</Type><Extend>true</Extend></CreatePartition></CreatePartitions><ModifyPartitions><ModifyPartition wcm:action="add"><Order>1</Order><PartitionID>1</PartitionID><Format>FAT32</Format><Label>System</Label></ModifyPartition><ModifyPartition wcm:action="add"><Order>2</Order><PartitionID>3</PartitionID><Format>NTFS</Format><Label>Windows</Label><Letter>C</Letter></ModifyPartition></ModifyPartitions></Disk><WillShowUI>OnError</WillShowUI></DiskConfiguration><ImageInstall><OSImage><InstallFrom><MetaData wcm:action="add"><Key>/IMAGE/INDEX</Key><Value>1</Value></MetaData></InstallFrom><InstallTo><DiskID>0</DiskID><PartitionID>3</PartitionID></InstallTo><WillShowUI>OnError</WillShowUI></OSImage></ImageInstall><UserData><AcceptEula>true</AcceptEula><FullName>Nextgen QA</FullName><Organization>Software Next Generation</Organization></UserData>'''
ps="powershell.exe -NoProfile -ExecutionPolicy Bypass -Command \"$d=(Get-Volume | Where-Object FileSystemLabel -eq 'NEXTGEN_QA' | Select-Object -First 1).DriveLetter; & ($d + ':\\first-logon.ps1')\""
shell=f'''<OOBE><HideEULAPage>true</HideEULAPage><HideOnlineAccountScreens>true</HideOnlineAccountScreens><HideWirelessSetupInOOBE>true</HideWirelessSetupInOOBE><ProtectYourPC>1</ProtectYourPC></OOBE><UserAccounts><LocalAccounts><LocalAccount wcm:action="add"><Name>NextgenQA</Name><DisplayName>Nextgen QA</DisplayName><Group>Administrators</Group><Password><Value>{html.escape(password)}</Value><PlainText>true</PlainText></Password></LocalAccount></LocalAccounts></UserAccounts><AutoLogon><Enabled>true</Enabled><LogonCount>1</LogonCount><Username>NextgenQA</Username><Password><Value>{html.escape(password)}</Value><PlainText>true</PlainText></Password></AutoLogon><FirstLogonCommands><SynchronousCommand wcm:action="add"><Order>1</Order><Description>Validate installed Nextgen products</Description><CommandLine>{html.escape(ps)}</CommandLine></SynchronousCommand></FirstLogonCommands>'''
xml='<?xml version="1.0" encoding="utf-8"?><unattend xmlns="urn:schemas-microsoft-com:unattend" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State"><settings pass="windowsPE">'+component('Microsoft-Windows-International-Core-WinPE','<SetupUILanguage><UILanguage>en-US</UILanguage></SetupUILanguage>'+locale)+component('Microsoft-Windows-Setup',setup)+'</settings><settings pass="specialize">'+component('Microsoft-Windows-Shell-Setup','<ComputerName>NEXTGEN-WIN11</ComputerName><TimeZone>FLE Standard Time</TimeZone>')+'</settings><settings pass="oobeSystem">'+component('Microsoft-Windows-International-Core',locale)+component('Microsoft-Windows-Shell-Setup',shell)+'</settings></unattend>'
(seed/'Autounattend.xml').write_text(xml);(seed/'Autounattend.xml').chmod(0o600)
shutil.copy2(root/'packaging/windows-vm/first-logon.ps1',seed/'first-logon.ps1');(seed/'qa-media.marker').write_text('Nextgen Windows QA installation media')
(seed/'tests').mkdir(exist_ok=True)
for name in ['offline-app-check.mjs','report-examples-browser.mjs','close-desktop.mjs','capture-native.mjs']:shutil.copy2(root/'tests'/name,seed/'tests'/name)
for name in ['node-v24.22.2-win-x64.zip','virtio-win-guest-tools.exe']:shutil.copy2(work/'media'/name,seed/name)
if not args.bootstrap:
 shutil.copytree(work/'consumer',seed/'consumer',dirs_exist_ok=True)
installer_manifest=[]
for product in ([] if args.bootstrap else ['components','reports']):
 files=list((root/'artifacts/installer-sdk1'/product/'windows').glob('*-sdk1-win-x64.exe'));assert len(files)==1 and files[0].stat().st_size>100_000_000,product
 installer_manifest.append({'product':product,'filename':files[0].name,'sha256':hashlib.file_digest(files[0].open('rb'),'sha256').hexdigest().upper()})
 target=seed/'installers'/product;target.mkdir(parents=True,exist_ok=True);shutil.copy2(files[0],target/files[0].name)
(seed/'installers.json').write_text(json.dumps(installer_manifest,indent=2))
subprocess.run(['xorriso','-as','mkisofs','-J','-R','-V','NEXTGEN_QA','-o',str(work/'autounattend.iso'),str(seed)],check=True)
(work/'autounattend.iso').chmod(0o600)
seed.chmod(0o700)
print('Prepared QA media; credentials retained privately in',credentials)
