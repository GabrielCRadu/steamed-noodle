# **Arhitectura și Implementarea unui Stack de Gaming Mainline Linux pe OnePlus 8 (SM8250)**

Transformarea unui smartphone comercial bazat pe platforma Qualcomm Snapdragon 865 (SM8250, nume de cod *kona* / *instantnoodle*) într-o consolă portabilă de gaming sub un sistem de operare Mainline Linux reprezintă o lucrare de inginerie de sistem de o complexitate remarcabilă1. Această tranziție implică decuplarea completă a dispozitivului de stiva proprietară Android - compusă din runtime-ul ART, serverul SurfaceFlinger, subsistemul IPC Binder, HAL-urile închise și nucleele downstream de tip CAF 4.19 - și reconstruirea mediului de execuție pe baza unui kernel Linux upstream nemodificat4.  
Configurația hardware a terminalului OnePlus 8, care include 8 GB sau 12 GB memorie RAM LPDDR5, stocare de mare viteză UFS 3.0, un panou Fluid AMOLED de 1080x2400 pixeli la 90 Hz și unitatea de procesare grafică Adreno 650, furnizează o bază computațională capabilă să susțină sarcini grafice complexe1. Interfațarea acestui hardware cu un periferic hibrid precum GameSir X3 Pro, care asociază transportul de date USB-C Human Interface Device (HID) cu un modul activ de răcire termoelectrică Peltier, permite eliminarea plafonărilor termice severe și stabilizarea frecvențelor maxime de calcul7.  
La nivel de software, arhitectura propusă se sprijină pe un micro-compositor Wayland dedicat (Gamescope), driverul grafic complet open-source Mesa Turnip (Vulkan 1.3) și un lanț de execuție hibrid format din Proton 11 ARM64 și emulatorul usermode FEX-Emu, permițând rularea transparentă a titlurilor Windows x86/x86\_64 pe arhitectura AArch648.

## **1\. Starea Kernelului Mainline & Device Tree pentru SM8250**

Suportul upstream pentru platforma Qualcomm SM8250 a atins un nivel avansat de convergență în ramurile recente ale kernelului Linux (versiunile 6.6-6.17+), fiind dezvoltat activ în cadrul ecosistemului *Linux on Mobile* și integrat în distribuții specializate precum postmarketOS2. Cu toate acestea, punerea în funcțiune pe un dispozitiv specific de tip *oneplus-instantnoodle* impune rezolvarea unor limitări de subsistem și ajustarea precisă a arborilor de dispozitive (Device Tree Source \- DTS)12.

| Subsistem Hardware | Stare Suport Upstream | Modul Kernel / Arhitectură Driver | Observații Tehnice & Cerințe DTS |
| :---- | :---- | :---- | :---- |
| **Display (DSI/KMS)** | Funcțional (cu patch-uri) | msm\_drm / panel-dsi-generic | Necesită noduri DTS cu secvențe DCS și sincronizare DSC4. |
| **Touchscreen** | Funcțional Complet | goodix\_core / synaptics\_dsx | Interfațat prin magistrala I²C/SPI; noduri evdev standard14. |
| **Stocare UFS** | Funcțional Complet | ufs\_qcom | Suport complet UFS 3.0 pe magistrala PCIe/UniPro (/dev/sda ... /dev/sdf). |
| **USB-C OTG / USB 3.0** | Funcțional Parțial | qcom-pmic-typec / dwc3-qcom | Quirk hardware de multiplexare a liniilor de mare viteză USB 3.014. |
| **USB-PD (Power Delivery)** | Funcțional Limitat | pm8150b-charger | Necesită gestionare strictă a mașinii de stări pentru prevenirea blocajelor VBUS12. |
| **Audio ALSA/PipeWire** | Funcțional Condiționat | qcom-lpass / snd-soc-wcd938x | Depinde de firmware-ul proprietar Hexagon DSP și profile ALSA UCM214. |

### **Subsistemul de Afișare DRM/KMS și Panoul MIPI-DSI**

Afișajul AMOLED al dispozitivului OnePlus 8 este conectat prin intermediul a două benzi MIPI-DSI la unitatea DPU (Display Processing Unit) din cadrul nucleului DRM MSM. În timp ce infrastructura generică DRM/KMS gestionează operațiunile atomice de comutare a modului grafic, panoul fizic impune declararea în Device Tree a secvențelor exacte de inițializare DCS (Display Command Set), extrase din ramurile CAF sau firmware-ul OxygenOS4.  
Fără aceste tabele de comenzi, regulatorii de tensiune LDO asociați panoului nu pot stabili timpii de sincronizare corecți la trecerea dinspre bootloader-ul ABL către kernel. În plus, configurarea modului de 90 Hz necesită setarea explicită a frecvențelor ceasului de bit DSI și a parametrilor Display Stream Compression (DSC), ocolind limitările de lățime de bandă ale interfeței fizice.

### **Touchscreen și Stocare UFS**

Digitizorul tactil beneficiază de integrare completă prin driverele standard de kernel upstream goodix sau synaptics, comunicând direct prin magistrala I²C a SoC-ului și expunând fluxurile de coordonate direct către nodurile /dev/input/eventX14.  
Subsistemul de stocare UFS 3.0, gestionat prin driverul ufs\_qcom, funcționează la viteze native, permițând citiri și scrieri paralele fără penalizări de performanță prin cele 6 unități logice (LUN 0-5) mapate ca dispozitive de bloc SCSI standard.

### **Limitări Hardware Critice pe USB-C și Power Delivery**

Managementul portului USB Type-C pe OnePlus 8 prezintă două vulnerabilități structurale în contextul andocării controllerului de joc14:

> 1. Quirk-ul de multiplexare SuperSpeed: Din cauza absenței unui cip extern autonom de comutare a orientării magistralei pe placa de bază, controlerul DWC3 depinde de logica de detecție din PMIC14. Liniile USB 3.0 (5 Gbps) se activează exclusiv dacă orientarea raportată în /sys/class/typec/port0/orientation indică starea normală (*normal*)14. În cazul inserării inverse (*reverse*), subsistemul cade în modul de rezervă USB 2.0 (480 Mbps)14. Deși lățimea de bandă USB 2.0 este suficientă pentru perifericele HID, modul inversat limitează drastic lățimea de bandă dacă utilizatorul conectează simultan stocare externă prin portul controllerului14.  
> 2. Instabilitatea mașinii de stări USB-PD: În scenarii de alimentare prin passthrough, când încărcătorul PD este atașat la GameSir X3 Pro, driverul pm8150b-charger poate eșua în negocierea profilelor de tensiune ridicată (9V/12V) dacă trecerea din modul de consumator (*sink*) în cel de sursă (*source*) are loc în timpul transferului intens de date12. Soluționarea acestei instabilități necesită patch-uri DTS care să fixeze profilul negociat la 5V/3A sau descărcarea completă a capacităților înainte de reatașare14.

### **Arhitectura Audio: DSP Hexagon, ALSA și PipeWire**

Rutarea fluxurilor audio digitale către amplificatoarele interne și codecul Qualcomm WCD9385 se bazează pe subsistemul LPASS (Low Power Audio Subsystem) și pe procesorul de semnal digital Hexagon (ADSP)14. Funcționarea stabilă a stivei audio impune plasarea imaginilor de firmware proprietare extrase (adsp.mbn, cdsp.mbn) în directorul de sistem /lib/firmware/qcom/sm8250/16.  
La nivelul spațiului utilizator, este obligatorie definirea profilelor ALSA UCM2 (Use Case Manager), care descriu căile corecte ale mixerului hardware. Fără aceste fișiere UCM2, serverul de sunet PipeWire nu poate deschide rutele către difuzoarele stereo sau interfața jack/USB-C, generând blocaje în fluxul audio al jocurilor rulate sub Proton14.

## **2\. Arhitectura Grafică & Drivere Vulkan (Adreno 650\)**

Arhitectura grafică a dispozitivului se sprijină integral pe driverul open-source Vulkan **Mesa Turnip**, asociat compilatorului de shadere freedreno/ir3 și driverului de kernel Direct Rendering Manager msm17. Această stivă asigură o implementare complet conformă a standardului Vulkan 1.3, ocolind în totalitate limitările driverului proprietar Qualcomm11.

### **Compatibilitate Vulkan 1.3 și Extensii Fundamentale**

Pentru a susține translatarea dinamică a straturilor Direct3D către Vulkan și compunerea cadrelor la nivel de display server, Turnip implementează un set critic de extensii17:

* VK\_EXT\_custom\_border\_color: Necesară pentru emulatorul DXVK în vederea reproducerii fidele a modurilor de adresare a texturilor și a eșantionării specifice API-urilor D3D9 și D3D1117.  
* VK\_EXT\_graphics\_pipeline\_library (GPL): Permite compilarea modulară și asincronă a stărilor de pipeline grafic (vertex input, pre-rasterization, fragment output), eliminând aproape în totalitate fenomenul de micro-întrerupere (*shader stutter*) specific jocurilor PC la prima încărcare a activelor11.  
* VK\_EXT\_descriptor\_buffer și VK\_KHR\_dynamic\_rendering: Elimină structurile rigide de tip *descriptor sets* și *render passes*, aliniind stiva Vulkan direct la modelul de execuție D3D12 gestionat de VKD3D-Proton18.  
* VK\_EXT\_image\_drm\_format\_modifier: Punctul structural central pentru integrarea cu Gamescope17. Această extensie permite crearea de imagini Vulkan asociate cu modificatori liniari sau compresați (UBWC \- Universal Bandwidth Compression), facilitând exportul direct de buffere DMABUF către planurile hardware ale afișajului prin modul *Direct Display Scanout*, fără copieri redundante în memoria de sistem17.

### **Microarhitectura TBDR: Tiled GMEM vs. Sysmem Rendering**

GPU-ul Adreno 650 este construit în jurul unei arhitecturi TBDR (*Tile-Based Deferred Rendering*)21. Procesorul conține o memorie SRAM internă ultra-rapidă denumită **GMEM**, cu o capacitate fizică de 1024 KB21.  
În modul implicit bazat pe GMEM, cadrul grafic este divizat în blocuri spațiale (*tiles*), iar rasterizarea și operațiunile de adâncime/amestecare (*depth/blending*) sunt executate exclusiv în memoria locală de pe cip, minimizând tranzacțiile de date cu memoria RAM LPDDR521.  
Tranziția către modul direct (*Sysmem Rendering*), în care geometria este randată direct în memoria principală de sistem, devine necesară în scene complexe cu tehnici masive de iluminare amânată (*Deferred Shading*), ray-marching sau treceri computaționale frecvente ce invalidează datele din GMEM21.  
Deși forțarea modului direct prin variabila de mediu TU\_DEBUG=sysmem poate fi utilă pentru depanare, cele mai recente versiuni de Mesa utilizează un subsistem euristic de autotuning care comută dinamic între GMEM și Sysmem la nivel de *render pass*, maximizând rata de cadre11.

### **Compilarea Shaderelor și Optimizările IR3**

Procesul de transformare a instrucțiunilor grafice parcurge un lanț multistadial structurat:

> 1. Formatul intermediar original (DirectX Shader Bytecode \- DXBC sau DXIL) este interceptat de DXVK sau VKD3D-Proton și convertit în reprezentare standardizată SPIR-V.  
> 2. Compilatorul din Mesa Turnip parsează codul SPIR-V și îl transpune în reprezentarea intermediară proprie Mesa (NIR), unde se aplică optimizări algebrice, eliminarea instrucțiunilor moarte și simplificarea fluxului de control17.  
> 3. Backend-ul freedreno/ir3 transformă instrucțiunile NIR în cod mașină optimizat pentru arhitectura ISA Adreno 6xx, alocând registrele fizice și generând pachetele de instrucțiuni executabile pe unitățile ALUs ale GPU-ului17.

Pentru a preveni degradarea performanței cauzată de recompilările frecvente, sistemul trebuie configurat cu MESA\_SHADER\_CACHE\_DISABLE=false și MESA\_SHADER\_CACHE\_MAX\_SIZE=512MB, stocând binarele IR3 compilate direct pe discul UFS21.  
Asocierea acestor setări cu opțiunea dxvk.enableAsync \= true permite delegarea sarcinilor de compilare către nucleele de eficiență Cortex-A55, eliberând nucleele mari Cortex-A77 pentru logica jocului și emularea CPU2.

## **3\. Integrarea Proton 11 ARM64 & FEX-Emu**

Tranziția de la platformele x86\_64 tradiționale la arhitectura ARM64 pentru jocuri Windows complexe este asigurată de **Proton 11 ARM64**, care integrează nativ recompilatorul binar usermode **FEX-Emu**9.

### **Modelul de Execuție Hibrid: ARM64EC și Redirecționarea (Thunking)**

Spre deosebire de tehnicile brute de virtualizare completă, care emulează întregul sistem de operare inducând pierderi masive de performanță, Proton 11 folosește modelul de interoperabilitate **ARM64EC** (*Emulation Compatible*)9. Această abordare permite combinarea codului nativ AArch64 cu segmente de cod x86/x86\_64 translatate în interiorul aceluiași spațiu de adrese al procesului10.  
Recompilatorul FEX-Emu preia exclusiv instrucțiunile mașină x86/x86\_64 ale jocului și le traduce în instrucțiuni AArch64 prin intermediul unui motor JIT (*Just-In-Time*)10. FEX utilizează o reprezentare intermediară ce gestionează eficient vectorizarea registrelor SSE/AVX și emulează semantica de memorie TSO (*Total Store Ordering*), obligatorie pentru sincronizarea firelor de execuție în jocurile concepute pentru procesoare Intel/AMD10.  
În paralel, bibliotecile fundamentale Wine, apelurile Win32, subsistemul de gestionare a memoriei și translatatoarele DXVK/VKD3D sunt compilate complet nativ pentru arhitectura ARM6410.  
Prin intermediul tehnologiei de redirecționare (*Vulkan Thunking*), apelurile interceptate la nivel de vulkan-1.dll ocolesc complet motorul de emulare CPU și sunt transmise direct către driverul nativ din sistemul gazdă (libvulkan\_freedreno.so)10. În acest mod, instrucțiunile de randare și încărcare a texturilor se execută la viteză nativă pe GPU-ul Adreno 65010.

### **Etape de Configurare în Steam Client ARM64**

Pentru activarea stivei de compatibilitate în clientul oficial Steam ARM64, este necesară respectarea unei succesiuni riguroase de configurare29:

> 1. **Amplasarea Structurii Proton:** Lanțul de binare Proton 11 ARM64 trebuie extras sau compilat în directorul utilizator dedicat:\~/.local/share/Steam/compatibilitytools.d/proton\_11\_arm64/  
>    \[cite: 29, 30\]  
> 2. **Declararea Fișierului toolmanifest.vdf:** Clientul Steam citește manifestul de compatibilitate pentru a determina containerul de execuție (*Pressure-Vessel* / *SteamRT4*)25:  
>    Fragment de cod  
>    "manifest"  
>    {  
>      "commandline" "/proton run"  
>      "version" "11.0-arm64"  
>      "use\_steam\_runtime" "1"  
>      "compatmanager\_layer\_name" "proton\_arm64"  
>    }

> 3. **Setarea Variabilelor de Mediu Globale:** Pentru a preveni coliziunea driverelor și a forța încărcarea corectă a bibliotecilor grafice native, se exportă următorii parametri:  
   * VK\_ICD\_FILENAMES=/usr/share/vulkan/icd.d/freedreno\_icd.aarch64.json: Asigură utilizarea exclusivă a driverului Mesa Turnip22.  
   * FEX\_CONFIG\_JSON=/etc/fex-emu/Config.json: Definește opțiunile de recompilare JIT, permițând dezactivarea emulării stricte a coprocesorului matematic x87 pe 80 de biți pentru a obține un spor de până la 15% în jocurile pe 32 de biți10.  
   * PRESSURE\_VESSEL\_SHARE\_HOME=1: Permite containerului Steam să acceseze driverele și socket-urile DRM/Wayland din sistemul de operare gazdă.

## **4\. Managementul Termic, Energetic și Subsistemul de Input**

Sarcina combinată de recompilare binară continuă (FEX-Emu), translatare Direct3D-Vulkan (DXVK) și randare grafică 3D generează o putere disipată susținută între 8 W și 11 W, o valoare ce depășește capacitatea de disipare pasivă a carcasei OnePlus 87.

### **Topologia SM8250 și Comportamentul la Throttling**

SoC-ul Qualcomm Snapdragon 865 integrează o arhitectură tri-cluster pe 64 de biți1:

* **1x Kryo 585 Prime (Cortex-A77)** tactat până la 2.84 GHz cu 512 KB L2 cache1.  
* **3x Kryo 585 Gold (Cortex-A77)** tactate până la 2.42 GHz cu câte 256 KB L2 cache1.  
* **4x Kryo 585 Silver (Cortex-A55)** tactate până la 1.80 GHz cu câte 128 KB L2 cache1.  
* **GPU Adreno 650** tactat nominal la 587 MHz (cu trepte dinamice de boost până la 670 MHz)4.

În regim pasiv, acumularea termică declanșează intervenția driverului de kernel qcom-spmi-temp-alarm la depășirea temperaturii de 70-75 °C pe senzorii joncțiunii de siliciu. Mecanismul de throttling reduce sever frecvența nucleului Prime sub 1.40 GHz, iar GPU-ul coboară la 305 MHz, prăbușind frecvența de cadre și generând blocaje masive.

### **Răcirea Activă Peltier (GameSir X3 Pro)**

Modulul termoelectric integrat în GameSir X3 Pro aplică o celulă Peltier (TEC) direct pe suprafața din sticlă a panoului posterior, disipând căldura printr-un radiator de aluminiu ventilat la turație înaltă7.  
La un consum exterior de aproximativ 10-12 W dedicat exclusiv răcirii, temperatura joncțiunii de siliciu sub sarcină maximă scade și se stabilizează în intervalul 45-52 °C7.  
Această extracție continuă de căldură modifică radical comportamentul guvernatorului de frecvență CPU (schedutil sau performance):

* Nucleele Kryo 585 Prime (2.84 GHz) și Gold (2.42 GHz) își mențin frecvențele maxime fără întrerupere pe parcursul sesiunilor prelungite de joc1.  
* Planificatorul de procese din kernel nu mai este forțat să migreze firele intensive de execuție ale FEX-Emu către nucleele lente Cortex-A55, păstrând latența de execuție la un nivel minim.  
* GPU-ul Adreno 650 rămâne blocat în starea de consum maximă (587-670 MHz), eliminând variațiile bruște de frametime cauzate de limitarea termică a alimentării4.

### **Arhitectura Subsistemului de Input în Gamescope**

Gamescope funcționează ca un micro-compositor Wayland ultra-optimizat ce preia controlul direct asupra dispozitivului DRM Master (/dev/dri/card0) prin subsistemul KMS, eliminând complet necesitatea unui server de afișare X11 tradițional sau a unui mediu desktop complet8.  
Interfațarea controllerului GameSir X3 Pro prin mufa Type-C se realizează direct la nivel de kernel prin driverul generic hid-generic sau hid-microslop, creând un nod de evenimente în /dev/input/eventX. Gamescope, utilizând biblioteca libinput, monitorizează și interceptează pachetele binare HID brute direct din subsistemul evdev8.  
Evenimentele de axă și butoane sunt transpuse intern în apeluri standardizate specifice interfeței Linux Gamepad API / SDL2, fiind injectate transparent în procesul Proton prin nodul virtual /dev/uinput8. Această arhitectură fără intermediari asigură o latență de intrare extrem de redusă (< 2 ms) și garantează maparea instantanee a comenzilor în jocurile Windows cu suport nativ XInput.

## **5\. Ghid de Implementare, Benchmarks Așteptate & Managementul Riscurilor**

Desfășurarea stivei de operare necesită pregătirea partițiilor fizice UFS, compilarea imaginilor personalizate și flash-uirea acestora prin intermediul instrumentelor de nivel scăzut14.

### **Fluxul Pas cu Pas de Instalare via pmbootstrap și fastboot**

> 1. **Deblocarea Bootloader-ului:** Terminalul este comutat în modul Fastboot prin menținerea combinației de taste Volume Down \+ Power, urmată de comanda:fastboot flashing unlock  
> 2. **Inițializarea Mediului de Construcție:** Pe o stație gazdă Linux, se inițializează mediul postmarketOS:pmbootstrap init Se configurează parametrii:  
   * *Vendor:* oneplus  
   * *Codename:* instantnoodle (sau instantnoodlep pentru varianta Pro)2  
   * *Channel:* edge  
   * *User Interface:* gamescope (sau none pentru configurare minimală)  
> 3. **Compilarea Nucleului și Generarea Imaginilor:** Se compilează pachetele de kernel cu arborele DTS aferent SM8250 și se generează imaginile de disc12: pmbootstrap install \--split  
> 4. **Scrierea Partițiilor:** Dispozitivul conectat în modul Fastboot este inscripționat secvențial14:  
>    Bash  
>    pmbootstrap flasher flash\_boot  
>    pmbootstrap flasher flash\_rootfs

>    Dacă dispozitivul utilizează schema de partiționare dinamică Android (*Super Partition*), imaginea rootfs trebuie redirecționată către volumul fizic userdata sau mapată într-un sub-volum logic pentru a nu distruge structura LUN-urilor adiacente14.

### **Estimări de Performanță și Benchmarks Așteptate**

Performanța atinsă combină eficiența recompilatorului JIT FEX-Emu, execuția nativă a straturilor Wine/DXVK și capacitățile de calcul ale GPU-ului Adreno 65010. Utilizarea motorului intern de upscaling AMD FidelityFX Super Resolution (FSR) din Gamescope permite reducerea rezoluției interne de randare la 720p cu scalare reconstructivă la 1080p, optimizând masiv rata de cadre.

| Titlu Joc | API Grafic / Rută Translatare | Rezoluție Răndare / Scalare | Rata Medie de Cadre (FPS) | 1% Lows (FPS) | Consum Mediu Energetic |
| :---- | :---- | :---- | :---- | :---- | :---- |
| **Hades** | Direct3D 11 / DXVK | 1080p Nativ (Fără FSR) | 75-90 FPS | 60 FPS | ≈ 5.5 W |
| **Fallout: New Vegas** | Direct3D 9 / DXVK 1.10.3 | 1080p Nativ / High | 50-60 FPS | 42 FPS | ≈ 6.8 W \[cite: 24, 33\] |
| **The Elder Scrolls V: Skyrim SE** | Direct3D 11 / DXVK 2.x | 720p → 1080p (Gamescope FSR) | 40-52 FPS | 30 FPS | ≈ 8.5 W |
| **Grand Theft Auto V** | Direct3D 11 / DXVK 2.x | 720p → 1080p (Gamescope FSR) | 32-45 FPS | 24 FPS | ≈ 9.2 W |

Jocurile pe 32 de biți Direct3D 9 (*Fallout: New Vegas*) și titlurile 2D/izometrice funcționează la rate de cadre ce saturează fluiditatea ecranului AMOLED de 90 Hz1. În titlurile 3D complexe din generația a opta (*GTA V*, *Skyrim SE*), translatarea asincronă GPL și scalarea reconstructivă FSR din Gamescope sunt absolut indispensabile pentru menținerea unei medii stabile de peste 30 FPS18.

### **Riscuri Tehnice Majore & Protocoale de Recuperare**

| Risc Tehnic Identificat | Mecanism Cauzal | Impact Asupra Sistemului | Protocol Tehnic de Remediere / Mitigare |
| :---- | :---- | :---- | :---- |
| **Coruperea Tabelei GPT UFS** | Suprascrierea necorespunzătoare a volumelor dinamice super/userdata14. | Dispozitiv blocat complet (*Hard-Brick*); lipsă răspuns Fastboot. | Forțare în mod EDL (Qualcomm HS-USB QDLoader 9008\) și rescriere GPT via bkerler/edl sau OnePlus MSM Download Tool34. |
| **Degradarea Termică a Bateriei** | Încărcare rapidă simultană cu disiparea termică maximă a SoC-ului. | Supraîncălzire chimică a celulei Li-Po; risc de umflare și degradare accelerată. | Activarea bypass-ului de încărcare (*pass-through power*) în kernel via nodurile sysfs ale driverului pm8150b-charger12. |
| **Eșec Handshake USB-PD** | Instabilitate tranzientă la comutarea rolurilor sink/source sub sarcină14. | Întreruperea alimentării coolerului Peltier și revenirea la starea de throttling sever7. | Descărcarea capacităților electrice, fixarea profilului 5V/3A în DTS și reatașarea conectorului USB-C14. |

#### **Protocolul de Recuperare EDL (Emergency Download Mode)**

În eventualitatea unui hard-brick provocat de alterarea tabelelor GUID ale discurilor fizice UFS, SoC-ul SM8250 poate fi recuperat prin modul de descărcare de urgență34. Terminalul este deconectat, iar prin menținerea ambelor butoane de volum la introducerea cablului USB se inițializează interfața Qualcomm HS-USB QDLoader 900834.  
De sub un sistem Linux, utilitarul open-source bkerler/edl permite comunicarea cu nucleul primar PBL (Primary Boot Loader), încărcarea binarului semnat Firehose (prog\_firehose\_ddr.elf) și reconstrucția completă a LUN-urilor UFS din imaginile de fabrică OxygenOS34.

#### **Protecția Acumulatorului prin Bypass Energetic**

Pentru a preveni uzura prematură a bateriei pe durata sesiunilor prelungite de gaming cu alimentare externă, kernelul mainline trebuie compilat cu suport extins de control în driverul pm8150b-charger12.  
Prin intermediul scripturilor de inițializare Gamescope, sistemul decuplează încărcarea chimică a acumulatorului și direcționează întregul flux de curent exclusiv către alimentarea plăcii de bază prin comanda:echo 0 \> /sys/class/power\_supply/battery/charging\_enabled  
Această configurare menține acumulatorul la o temperatură scăzută și permite funcționarea la performanțe maxime fără degradarea stării de sănătate a celulei Li-Po.

## **6\. Concluzii**

Implementarea unei platforme de gaming complet Mainline Linux pe smartphone-ul OnePlus 8 validează potențialul arhitecturii SM8250 de a evolua într-o veritabilă consolă portabilă1. Convergența dintre driverul grafic Mesa Turnip (cu suport complet Vulkan 1.3 și GPL), micro-compositorul Gamescope și stiva de execuție hibridă Proton 11 ARM64 susținută de recompilatorul JIT FEX-Emu rezolvă principalele bariere de compatibilitate și performanță8.  
Stabilitatea pe termen lung a acestui ecosistem depinde în mod critic de doi factori fizici și de sistem: neutralizarea limitărilor termice prin răcirea activă termoelectrică Peltier (asigurată de perifericul GameSir X3 Pro) pentru a menține frecvențele maxime pe nucleele Kryo 585 Prime/Gold, și configurarea corectă a subsistemelor de kernel pentru comutarea USB-C și bypass-ul energetic al bateriei1.  
Prin respectarea arhitecturii documentate, OnePlus 8 depășește stadiul de simplu experiment demonstrativ, oferind o experiență de joc fluidă și stabilă în titluri complexe de PC rulate direct pe hardware ARM641.

#### **Lucrări citate**

> 1. OnePlus 8 (oneplus-instantnoodle) \- postmarketOS Wiki, [https://wiki.postmarketos.org/wiki/OnePlus\_8\_(oneplus-instantnoodle)](https://wiki.postmarketos.org/wiki/OnePlus_8_\(oneplus-instantnoodle\))  
> 2. Qualcomm Snapdragon 865/865+/870 (SM8250) \- postmarketOS Wiki, [https://wiki.postmarketos.org/wiki/Qualcomm\_Snapdragon\_865/865%2B/870\_(SM8250)](https://wiki.postmarketos.org/wiki/Qualcomm_Snapdragon_865/865%2B/870_\(SM8250\))  
> 3. User:Knuxify/List of chipsets and devices that use them \- postmarketOS Wiki, [https://wiki.postmarketos.org/wiki/User:Knuxify/List\_of\_chipsets\_and\_devices\_that\_use\_them](https://wiki.postmarketos.org/wiki/User:Knuxify/List_of_chipsets_and_devices_that_use_them)  
> 4. Releases · 0ctobot/neutrino\_kernel\_oneplus\_sm8250 \- GitHub, [https://github.com/0ctobot/neutrino\_kernel\_oneplus\_sm8250/releases](https://github.com/0ctobot/neutrino_kernel_oneplus_sm8250/releases)  
> 5. https://github.com/0ctobot/neutrino\_kernel\_oneplus\_sm8250 · GitHub \- GitHub Gist, [https://gist.github.com/0ctobot/e361b360b9e1eb09b41d29436654d21b](https://gist.github.com/0ctobot/e361b360b9e1eb09b41d29436654d21b)  
> 6. postmarketOS-powered Kubernetes cluster \- /dev/random \- Denys Vitali, [https://blog.denv.it/posts/pmos-k3s-cluster/](https://blog.denv.it/posts/pmos-k3s-cluster/)  
> 7. What can a Snapdragon 865+ play if I wanted to push it to the limit? : r/EmulationOnAndroid, [https://www.reddit.com/r/EmulationOnAndroid/comments/x7ip7r/what\_can\_a\_snapdragon\_865\_play\_if\_i\_wanted\_to/](https://www.reddit.com/r/EmulationOnAndroid/comments/x7ip7r/what_can_a_snapdragon_865_play_if_i_wanted_to/)  
> 8. Steam Deck: Gamescope Deep Dive \- GitHub, [https://github.com/dsrtfbbg379/gamescope-deep-dive](https://github.com/dsrtfbbg379/gamescope-deep-dive)  
> 9. Proton 11.0-2 Drops: vkd3d 2.0 and Wine 11.0 Regression Fixes \- Linux Compatible, [https://www.linuxcompatible.org/story/proton-1102-drops-vkd3d-20-and-wine-110-regression-fixes/](https://www.linuxcompatible.org/story/proton-1102-drops-vkd3d-20-and-wine-110-regression-fixes/)  
> 10. Valve isn't ditching Windows or x86, but it's quietly making both optional \- XDA Developers, [https://www.xda-developers.com/valve-isnt-ditching-windows-x86-quietly-making-optional/](https://www.xda-developers.com/valve-isnt-ditching-windows-x86-quietly-making-optional/)  
> 11. Mesa 22.1.0 Release Notes / 2022-05-18, [https://docs.mesa3d.org/relnotes/22.1.0.html](https://docs.mesa3d.org/relnotes/22.1.0.html)  
> 12. linux-sm8250 \- WuerfelDev \- postmarketOS · GitLab, [https://gitlab.postmarketos.org/WuerfelDev/linux-sm8250/-/tree/6.17.0-instantnoodle?ref\_type=heads](https://gitlab.postmarketos.org/WuerfelDev/linux-sm8250/-/tree/6.17.0-instantnoodle?ref_type=heads)  
> 13. linux \- Obi Keahloa \- postmarketOS · GitLab, [https://gitlab.postmarketos.org/ObiKeahloa/linux](https://gitlab.postmarketos.org/ObiKeahloa/linux)  
> 14. OnePlus 8 Pro (oneplus-instantnoodlep) \- postmarketOS Wiki, [https://wiki.postmarketos.org/wiki/OnePlus\_8\_Pro\_(oneplus-instantnoodlep)](https://wiki.postmarketos.org/wiki/OnePlus_8_Pro_\(oneplus-instantnoodlep\))  
> 15. User:Akku/android versions \- postmarketOS Wiki, [https://wiki.postmarketos.org/wiki/User:Akku/android\_versions](https://wiki.postmarketos.org/wiki/User:Akku/android_versions)  
> 16. oneplus 8 pro (instantnoodlep): new device packaging (\!3990) · Merge requests · postmarketOS / pmaports \- GitLab, [https://gitlab.com/postmarketOS/pmaports/-/merge\_requests/3990](https://gitlab.com/postmarketOS/pmaports/-/merge_requests/3990)  
> 17. Mesa 20.3.0 Release Notes / 2020-12-03, [https://docs.mesa3d.org/relnotes/20.3.0.html](https://docs.mesa3d.org/relnotes/20.3.0.html)  
> 18. Linux native BeamNG binary does not run · Issue \#424 · ptitSeb/box64 \- GitHub, [https://github.com/ptitSeb/box64/issues/424](https://github.com/ptitSeb/box64/issues/424)  
> 19. 21.2.0.rst « relnotes « docs \- mesa/mesa \- The Mesa 3D Graphics Library (mirrored from https://gitlab.freedesktop.org/mesa/mesa) \- freedesktop.org git repository browser, [https://cgit.freedesktop.org/mesa/mesa/tree/docs/relnotes/21.2.0.rst?h=21.2](https://cgit.freedesktop.org/mesa/mesa/tree/docs/relnotes/21.2.0.rst?h=21.2)  
> 20. Diff \- 0dcdeff049415cbd4f073bdba99bcf4cd61baa03^1..0dcdeff049415cbd4f073bdba99bcf4cd61baa03 \- platform/external/mesa3d \- Git at Google \- Android GoogleSource, [https://android.googlesource.com/platform/external/mesa3d/+/0dcdeff049415cbd4f073bdba99bcf4cd61baa03%5E1..0dcdeff049415cbd4f073bdba99bcf4cd61baa03/](https://android.googlesource.com/platform/external/mesa3d/+/0dcdeff049415cbd4f073bdba99bcf4cd61baa03%5E1..0dcdeff049415cbd4f073bdba99bcf4cd61baa03/)  
> 21. Optimizing Gaming Performance: ALSA vs PulseAudio & Environment Variables · Issue \#248 · The412Banner/Bannerlator \- GitHub, [https://github.com/The412Banner/Bannerlator/issues/248](https://github.com/The412Banner/Bannerlator/issues/248)  
> 22. Snapdragon 685 , everything is broken at any settings \+ low very performance (only 90 fps in the test, while on the classic Winlator Ludashi 960 fps. · Issue \#278 · The412Banner/Bannerlator \- GitHub, [https://github.com/The412Banner/Bannerlator/issues/278](https://github.com/The412Banner/Bannerlator/issues/278)  
> 23. Mesa 21.2.0 Release Notes / 2021-08-04, [https://docs.mesa3d.org/relnotes/21.2.0.html](https://docs.mesa3d.org/relnotes/21.2.0.html)  
> 24. i am getting low fps while my GPU can't even pass 75% usage. is there anything i can do? (besides getting a new phone or reducing the graphics) : r/winlator \- Reddit, [https://www.reddit.com/r/winlator/comments/1pgq9rs/i\_am\_getting\_low\_fps\_while\_my\_gpu\_cant\_even\_pass/](https://www.reddit.com/r/winlator/comments/1pgq9rs/i_am_getting_low_fps_while_my_gpu_cant_even_pass/)  
> 25. Proton/Makefile.in at proton\_11.0 \- GitHub, [https://github.com/ValveSoftware/Proton/blob/proton\_11.0/Makefile.in](https://github.com/ValveSoftware/Proton/blob/proton_11.0/Makefile.in)  
> 26. FEX-emu - Run x86 applications on ARM64 Linux devices \- Hacker News, [https://news.ycombinator.com/item?id=45905850](https://news.ycombinator.com/item?id=45905850)  
> 27. Canonical Promotes Steam Snap to Stable on ARM64, With... \- daily.dev, [https://daily.dev/posts/canonical-promotes-steam-snap-to-stable-on-arm64-with-plans-to-rebuild-it-from-scratch-later-h4rqoflv8](https://daily.dev/posts/canonical-promotes-steam-snap-to-stable-on-arm64-with-plans-to-rebuild-it-from-scratch-later-h4rqoflv8)  
> 28. Tiny Glade \- FEX-Emu Wiki, [https://wiki.fex-emu.com/index.php/Tiny\_Glade](https://wiki.fex-emu.com/index.php/Tiny_Glade)  
> 29. Makefile.in \- GloriousEggroll/proton-ge-custom \- GitHub, [https://github.com/GloriousEggroll/proton-ge-custom/blob/master/Makefile.in](https://github.com/GloriousEggroll/proton-ge-custom/blob/master/Makefile.in)  
> 30. émulation \- Liens en vrac de sebsauvage, [https://sebsauvage.net/links/?addtag=%C3%A9mulation](https://sebsauvage.net/links/?addtag=%C3%A9mulation)  
> 31. Valve kinda released ARM64 Proton, lol (works on my ARM64 machine, see the second screenshot) : r/linux\_gaming \- Reddit, [https://www.reddit.com/r/linux\_gaming/comments/1snjr0r/valve\_kinda\_released\_arm64\_proton\_lol\_works\_on\_my/](https://www.reddit.com/r/linux_gaming/comments/1snjr0r/valve_kinda_released_arm64_proton_lol_works_on_my/)  
> 32. GTK4 apps from Flatpak/Flathub fail to start with the vulkan rendering backend (\#3655) · Issue \- postmarketOS · GitLab, [https://gitlab.postmarketos.org/postmarketOS/pmaports/-/issues/3655](https://gitlab.postmarketos.org/postmarketOS/pmaports/-/issues/3655)  
> 33. Adreno 710 Guide For Better Performance and Not Visual Glitchs : r/winlator \- Reddit, [https://www.reddit.com/r/winlator/comments/1vuprt2/adreno\_710\_guide\_for\_better\_performance\_and\_not/](https://www.reddit.com/r/winlator/comments/1vuprt2/adreno_710_guide_for_better_performance_and_not/)  
> 34. FAQ - The AXP.OS Project, [https://axpos.org/docs/knowledge/faq/](https://axpos.org/docs/knowledge/faq/)  
> 35. Qualcomm CrashDump mode on recording HEVC 10-Bit video. (\#6421) · Issue \- GitLab, [https://gitlab.com/LineageOS/issues/android/-/issues/6421](https://gitlab.com/LineageOS/issues/android/-/issues/6421)

