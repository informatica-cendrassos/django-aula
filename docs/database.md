# Base de dades del projecte DJAU

Aquest document és un esborrany de documentació de la base de dades del projecte. L'esquema principal està definit en models abstractes dins de diversos mòduls de `aula/apps/*`, i després es materialitzen com a models concrets en fitxers `models.py` del mateix paquet.

## 1. Visió general

El projecte és una aplicació educativa tipus Django amb la següent estructura funcional:

- Gestió d'alumnes, grups, cursos i nivells
- Horaris i franges lectives
- Gestió de classes i presència
- Incidències, sancions i expulsions
- Matrícula i pagaments
- Relació amb famílies i notificacions
- Sortides, viatges i permisos
- Tutoria i seguiment de l'alumnat
- Material i reserves
- Avaluació qualitativa
- Integració amb sistemes externs (Saga, Esfera, Kronowin, Untis, Gedac)

La majoria dels models reals hereten de classes abstractes per reutilitzar validacions, camps comuns i comportament.

## 2. Models principals per aplicació

### 2.1. `alumnes`

#### `Nivell`
- Camps principals: `nom_nivell`, `ordre_nivell`, `descripcio_nivell`, `anotacions_nivell`, `matricula_oberta`, `limit_matricula`, `taxes`, `preexclusiva`
- Relacions: `ForeignKey` a `sortides.TipusQuota` a `taxes`
- Propòsit: representa un nivell acadèmic (ESO, Batxillerat, CFGM, etc.) i els seus paràmetres de matrícula.

#### `Curs`
- Camps principals: `nivell`, `nom_curs`, `nom_curs_complert`, `data_inici_curs`, `data_fi_curs`, `confirmacio_oberta`, `limit_confirmacio`
- Relacions: `ForeignKey` a `alumnes.Nivell`
- Propòsit: defineix cada curs dins d'un nivell.

#### `Grup`
- Camps principals: `curs`, `nom_grup`, `descripcio_grup`
- Relacions: `ForeignKey` a `alumnes.Curs`
- Propòsit: agrupa l'alumnat per grup dins del curs.

#### `Alumne`
- Camps principals: `ralc`, `grup`, `nom`, `nom_sentit`, `cognoms`, `data_neixement`, `estat_sincronitzacio`, `correu`, `adreca`, `localitat`, `municipi`, `cp`, `tutors`, `centre_de_procedencia`, dades de responsables, etc.
- Relacions: `ForeignKey` a `alumnes.Grup`; també es relaciona amb altres entitats per claus externes i M2M des d'altres apps (sortides, responsables, incidències, pagaments, etc.)
- Propòsit: entitat central de l'alumnat i la informació acadèmica i de contacte.

#### `DadesAddicionalsAlumne`
- Camps principals: dades addicionals de l'alumnat, foto, informació específica de l'entitat
- Relacions: normalment s'utilitza com a extensió de l'alumnat
- Propòsit: emmagatzemar informació addicional de l'alumne fora del model base.

#### `AlumneGrupNom`, `AlumneNomSentit`, `AlumneGrup`, `AlumneNomSentitGrup`
- Tipus: proxies de `Alumne`
- Propòsit: presentacions alternatives de l'alumne per a llistats i ordenacions específiques.

---

### 2.2. `usuaris`

#### `Departament`
- Camps principals: informació del departament del centre
- Relacions: s'utilitza com a FK en sortides i altres processos de coordinació
- Propòsit: agrupar professorat i activitats organitzatives.

#### `Professor` (proxy sobre `User`)
- Camps principals: hereta de `django.contrib.auth.models.User`
- Relacions: `ForeignKey` des de múltiples entitats (`Impartir`, `ControlAssistencia`, `Sancio`, `Expulsio`, etc.)
- Propòsit: representa el professorat del centre i la relació amb horaris, guàrdies i seguiment.

#### `DadesAddicionalsProfessor`
- Camps principals: `clauDeCalendari`, `professor`, `foto`
- Relacions: `OneToOneField` a `Professor`
- Propòsit: guardar informació extra del professor, com ara foto o clau del calendari.

#### `Professional`
- Tipus: model proxy sobre `User`
- Propòsit: identifica perfils professionals no docents (psicologia, orientació, etc.).

#### `ResponsableUser`, `AlumneUser`, `ProfessorConserge`
- Tipus: proxies i managers sobre `User`
- Propòsit: segmentar usuaris segons el rol del sistema.

---

### 2.3. `assignatures`

#### `TipusDAssignatura`
- Camps principals: `tipus_assignatura`, `ambit_on_prendre_alumnes`, `capcelera`
- Relacions: no té FK principals, però s'utilitza com a FK des de `Assignatura`
- Propòsit: classificar assignatures segons àmbit i ús.

#### `Assignatura`
- Camps principals: `curs`, `tipus_assignatura`, `codi_assignatura`, `nom_assignatura`
- Relacions: `ForeignKey` a `alumnes.Curs` i `assignatures.TipusDAssignatura`
- Propòsit: definir cada matèria del pla acadèmic.

---

### 2.4. `aules`

#### `Aula`
- Camps principals: `nom_aula`, `descripcio_aula`, `disponibilitat_horaria`, `horari_lliure`, `reservable`
- Relacions: `ManyToMany` amb `horaris.FranjaHoraria` a través de `disponibilitat_horaria`
- Propòsit: representar una aula del centre i les seves restriccions de disponibilitat.

#### `ReservaAula`
- Camps principals: `aula`, `dia_reserva`, `hora_inici`, `hora_fi`, `hora`, `usuari`, `motiu`, `es_reserva_manual`
- Relacions: `ForeignKey` a `aules.Aula`, `horaris.FranjaHoraria` i `auth.User`
- Propòsit: reservar una aula per a una franja concreta.

---

### 2.5. `horaris`

#### `DiaDeLaSetmana`
- Camps principals: `n_dia_uk`, `n_dia_ca`, `dia_2_lletres`, `dia_de_la_setmana`, `es_festiu`
- Relacions: sense FKs directes de negoci
- Propòsit: catalogar els dies de la setmana i si són festius.

#### `FranjaHoraria`
- Camps principals: `hora_inici`, `hora_fi`, `nom_franja`
- Relacions: s'utilitza en classes, reserves, festius i sortides
- Propòsit: definir franges lectives que es repeteixen en l'horari del centre.

#### `Horari`
- Camps principals: `assignatura`, `professor`, `grup`, `dia_de_la_setmana`, `hora`, `nom_aula`, `aula`, `es_actiu`, `estat_sincronitzacio`
- Relacions: `ForeignKey` a `assignatures.Assignatura`, `usuaris.Professor`, `alumnes.Grup`, `horaris.DiaDeLaSetmana`, `horaris.FranjaHoraria`, `aules.Aula`
- Propòsit: representa una entrada d'horari concreta: una classe, grup i franja.

#### `Festiu`
- Camps principals: `curs`, `data_inici_festiu`, `franja_horaria_inici`, `data_fi_festiu`, `franja_horaria_fi`, `descripcio`
- Relacions: `ForeignKey` a `alumnes.Curs` i a dues franges horàries
- Propòsit: marcar períodes de vacances o dies festius al calendari acadèmic.

---

### 2.6. `presencia`

#### `Impartir`
- Camps principals: `horari`, `professor_guardia`, `professor_passa_llista`, `dia_impartir`, `dia_passa_llista`, `estat_neteja_aula`, `comentariImpartir`, `pot_no_tenir_alumnes`, `reserva`
- Relacions: `ForeignKey` a `horaris.Horari`, `usuaris.Professor`, `aules.ReservaAula`
- Propòsit: defineix una classe impartida en una data concreta, amb el seu estat d'assistència i estat de neteja de l'aula.

#### `EstatControlAssistencia`
- Camps principals: `codi_estat`, `nom_estat`, `pct_ausencia`
- Propòsit: estat de l'assistència (present, falta, retard, etc.).

#### `ControlAssistencia`
- Camps principals: `alumne`, `estat`, `impartir`, `professor`, `swaped`, `estat_backup`, `professor_backup`
- Relacions: `ForeignKey` a `alumnes.Alumne`, `presencia.EstatControlAssistencia`, `presencia.Impartir`, `usuaris.Professor`
- Propòsit: recull l'assistència de cada alumne en una sessió concreta.

#### `NoHaDeSerALAula`
- Propòsit: registre d'alumnes que no han d'estar a l'aula en un moment determinat; útil per a activitats o absències programades.
- Relació: normalment lligat a una presència o sessió concreta.

---

### 2.7. `incidencies`

#### `FrassesIncidenciaAula`
- Camps principals: `tipus`, `frase`
- Relacions: `ForeignKey` a `incidencies.TipusIncidencia`
- Propòsit: frases predefinides per registrar incidències amb text estàndard.

#### `TipusSancio`
- Camps principals: `tipus`, `carta_slug`, `justificar`
- Propòsit: classifica els tipus de sanció.

#### `Sancio`
- Camps principals: `professor`, `alumne`, `tipus`, `data_inici`, `franja_inici`, `data_fi`, `franja_fi`, `data_carta`, `motiu`, `obra_expedient`, `comentaris_cap_d_estudis`, `signat`, `impres`, `notificacions_familia`
- Relacions: `ForeignKey` a `usuaris.Professor`, `alumnes.Alumne`, `incidencies.TipusSancio`, `horaris.FranjaHoraria`; `ManyToMany` amb `usuaris.NotifUsuari`
- Propòsit: sanció aplicada a un alumne amb data, motiu i notificació a famílies.

#### `Expulsio`
- Camps principals: `estat`, `professor_recull`, `professor`, `control_assistencia`, `alumne`, `dia_expulsio`, `franja_expulsio`, `motiu`, `moment_comunicacio_a_tutors`, `tutor_contactat_per_l_expulsio`, `tramitacio_finalitzada`, `comentaris_cap_d_estudis`, `provoca_sancio`, `es_expulsio_per_acumulacio_incidencies`, `es_vigent`, `notificacions_familia`
- Relacions: `ForeignKey` a `usuaris.Professor`, `presencia.ControlAssistencia`, `alumnes.Alumne`, `horaris.FranjaHoraria`, `incidencies.Sancio`; `ManyToMany` amb `usuaris.NotifUsuari`
- Propòsit: registrar falta greu o expulsió de l'aula.

#### `TipusIncidencia`
- Camps principals: metadades del tipus d'incidència
- Relacions: s'utilitza com a FK en frases i incidències
- Propòsit: classificar incidències per tipus.

#### `Incidencia`
- Camps principals: data, alumne, tipus, professor, descripció i dades associades
- Relacions: `ForeignKey` a `alumnes.Alumne`, `incidencies.TipusIncidencia`, `usuaris.Professor`, `presencia.Impartir`, etc.
- Propòsit: registre d'incidències de l'alumnat a classe.

---

### 2.8. `avaluacioQualitativa`

#### `ItemQualitativa`
- Camps principals: `codi_agrupacio`, `text`, `nivells`
- Relacions: `ManyToMany` amb `alumnes.Nivell`
- Propòsit: frase reutilitzable dins d'una avaluació qualitativa.

#### `AvaluacioQualitativa`
- Camps principals: `nom_avaluacio`, `data_obrir_avaluacio`, `data_tancar_avaluacio`, `grups`, `data_obrir_portal_families`, `data_tancar_tancar_portal_families`
- Relacions: `ManyToMany` amb `alumnes.Grup`
- Propòsit: defineix un període d'avaluació amb grups i dates d'obertura/tancament.

#### `RespostaAvaluacioQualitativa`
- Camps principals: `qualitativa`, `alumne`, `professor`, `assignatura`, `item`, `frase_oberta`, `notificacions_familia`
- Relacions: `ForeignKey` a `avaluacioQualitativa.AvaluacioQualitativa`, `alumnes.Alumne`, `usuaris.Professor`, `assignatures.Assignatura`, `avaluacioQualitativa.ItemQualitativa`; `ManyToMany` amb `usuaris.NotifUsuari`
- Propòsit: resposta concreta d'un professor per a un alumne i assignatura dins d'una avaluació.

---

### 2.9. `missatgeria`

#### `Missatge`
- Camps principals: `data`, `remitent`, `text_missatge`, `enllac`, `tipus_de_missatge`
- Relacions: `ForeignKey` a `auth.User`
- Propòsit: enviar un missatge genèric a usuaris o grups del sistema.

#### `DetallMissatge`
- Camps principals: `missatge`, `detall`, `tipus`
- Relacions: `ForeignKey` a `missatgeria.Missatge`
- Propòsit: detall, avís o error associat a un missatge principal.

#### `Destinatari`
- Camps principals: `missatge`, `importancia`, `destinatari`, `moment_lectura`, `followed`
- Relacions: `ForeignKey` a `missatgeria.Missatge` i `auth.User`
- Propòsit: controlar l'entrega i lectura de cada missatge per destinatari.

---

### 2.10. `tutoria`

#### `SeguimentTutorial`
- Camps principals: `alumne`, `nom`, `cognoms`, `datadarreraactualitzacio`, `data_neixement`, `informacio_de_primaria`
- Relacions: `OneToOneField` a `alumnes.Alumne`
- Propòsit: registre principal del seguiment tutorial de cada alumne.

#### `ResumAnualAlumne`
- Camps principals: `seguiment_tutorial`, `curs_any_inici`, `text_resum`
- Relacions: `ForeignKey` a `tutoria.SeguimentTutorial`
- Propòsit: resum anual de cada alumne dins del seguiment tutorial.

#### `SeguimentTutorialPreguntes`
- Camps principals: `pregunta`, `ajuda_pregunta`, `es_pregunta_oberta`, `possibles_respostes`
- Propòsit: catàleg de preguntes del seguiment tutorial.

#### `SeguimentTutorialRespostes`
- Camps principals: `seguiment_tutorial`, `any_curs_academic`, `pregunta`, `resposta`, `ordre`, `professorQueInforma`
- Relacions: `ForeignKey` a `tutoria.SeguimentTutorial`
- Propòsit: respostes del seguiment per a cada curs acadèmic.

#### `Actuacio`
- Camps principals: `alumne`, `professional`, `moment_actuacio`, `qui_fa_actuacio`, `amb_qui_es_actuacio`, `assumpte`, `actuacio`
- Relacions: `ForeignKey` a `alumnes.Alumne` i `usuaris.Professional`
- Propòsit: registrar actuacions de tutoria o psicologia amb l'alumnat.

#### `Tutor`
- Camps principals: `professor`, `grup`
- Relacions: `ForeignKey` a `usuaris.Professor` i `alumnes.Grup`
- Propòsit: associació entre tutor i grup.

#### `TutorIndividualitzat`
- Camps principals: `professor`, `alumne`
- Relacions: `ForeignKey` a `usuaris.Professor` i `alumnes.Alumne`
- Propòsit: associació de tutor individual a un alumne concret.

#### `CartaAbsentisme`
- Camps principals: `alumne`, `carta_numero`, `tipus_carta`, `faltes_fins_a_data`, `faltes_des_de_data`, `professor`, `data_carta`, `faltes_incloses`, `nfaltes`, `impresa`
- Relacions: `ForeignKey` a `alumnes.Alumne` i `usuaris.Professor`
- Propòsit: generar i controlar cartes d'absentisme.

---

### 2.11. `relacioFamilies`

#### `EmailPendent`
- Camps principals: `subject`, `message`, `fromemail`, `toemail`
- Propòsit: gestionar correus pendents o no enviats.

#### `DocAttach`
- Camps principals: `fitxer`, `email`
- Relacions: `ForeignKey` a `relacioFamilies.EmailPendent`
- Propòsit: adjunts de missatges per correu.

#### `Responsable`
- Camps principals: `dni`, `nom`, `cognoms`, `parentiu`, `localitat`, `municipi`, `cp`, `adreca`, `telefon`, `correu`, `data_alta`, `data_baixa`, `user_associat`, `correu_relacio_familia`, `periodicitat_faltes`, `periodicitat_incidencies`, `motiu_bloqueig`
- Relacions: `OneToOneField` a `auth.User`; `ManyToMany` a `alumnes.Alumne`
- Propòsit: representar un responsable de família i la seva relació amb els alumnes.

---

### 2.12. `matricula`

#### `Matricula`
- Camps principals: `idAlumne`, `estat`, `any`, `curs`, `quota`, `alumne`, `preinscripcio`, `acceptar_condicions`, `acceptacio_en`, `confirma_matricula`, `curs_complet`, `quantitat_ufs`, `llistaufs`, `bonificacio`, `fracciona_taxes`, `nom`, `cognoms`, `centre_de_procedencia`, dades de responsables i contacte
- Relacions: `ForeignKey` a `alumnes.Curs`, `sortides.Quota`, `alumnes.Alumne`, `extPreinscripcio.Preinscripcio`
- Propòsit: gestionar la matrícula de cada alumne per a un curs concret.

#### `Document`
- Camps principals: `fitxer`, `matricula`
- Relacions: `ForeignKey` a `matricula.Matricula`
- Propòsit: adjuntar documents associats a la matrícula.

---

### 2.13. `sortides`

#### `TPV`
- Camps principals: `nom`, `codi`, `key`, `descripcio`, `entornReal`
- Propòsit: configuració de terminal de pagament virtual per a pagaments de sortides o quotes.

#### `Sortida`
- Camps principals: `estat`, `estat_sincronitzacio`, `tipus`, `subtipus`, `titol`, `ambit`, `ciutat`, `esta_aprovada_pel_consell_escolar`, `departament_que_organitza`, `comentari_organitza`, `alumnes_a_l_aula_amb_professor_titular`, `data_inici`, `franja_inici`, `data_fi`, `franja_fi`, `calendari_desde`, `calendari_finsa`, `calendari_public`, `materia`, `tipus_de_pagament`, `preu_per_alumne`, `codi_de_barres`, `informacio_pagament`, `termini_pagament`, `programa_de_la_sortida`, `condicions_generals`, `participacio`, `mitja_de_transport`, `empresa_de_transport`, `pagament_a_empresa_de_transport`, `pagament_a_altres_empreses`, `feina_per_als_alumnes_aula`, `comentaris_interns`, `professor_que_proposa`, `professors_responsables`, `altres_professors_acompanyants`, `tutors_alumnes_convocats`, `alumnes_convocats`, `alumnes_que_no_vindran`, `alumnes_justificacio`, `pagaments`, `tpv`
- Relacions: `ForeignKey` a `usuaris.Departament`, `horaris.FranjaHoraria`, `usuaris.Professor`, `sortides.TPV`; `ManyToMany` amb `usuaris.Professor` i `alumnes.Alumne`
- Propòsit: activitat escolar, excursió o sortida amb informació administrativa, logística, participants i pagaments.

#### `TipusQuota`
- Camps principals: `nom`
- Propòsit: categoritzar quotes (matrícula, transport, material, etc.).

#### `Quota`
- Camps principals: `importQuota`, `dataLimit`, `any`, `descripcio`, `curs`, `tpv`, `tipus`
- Relacions: `ForeignKey` a `alumnes.Curs`, `sortides.TPV`, `sortides.TipusQuota`
- Propòsit: quota associada a un curs o a un conjunt d'alumnes.

#### `Pagament`
- Camps principals: `alumne`, `sortida`, `data_hora_pagament`, `pagament_realitzat`, `ordre_pagament`, `quota`, `fracciona`, `importParcial`, `dataLimit`, `observacions`, `estat`, `notificacions_familia`
- Relacions: `ForeignKey` a `alumnes.Alumne`, `sortides.Sortida`, `sortides.Quota`; `ManyToMany` a `usuaris.NotifUsuari`
- Propòsit: registrar pagaments associats a sortides o quotes.

#### `QuotaPagament`, `SortidaPagament`
- Tipus: proxies de `Pagament`
- Propòsit: filtrar i etiquetar pagaments segons la seva procedència.

#### `NotificaSortida`
- Camps principals: `alumne`, `sortida`, `notificacions_familia`
- Relacions: `ForeignKey` a `alumnes.Alumne` i `sortides.Sortida`; `ManyToMany` a `usuaris.NotifUsuari`
- Propòsit: seguiment de notificacions relacionades amb sortides.

---

### 2.14. `material`

#### `Recurs`
- Camps principals: `nom_recurs`, `descripcio_recurs`, `disponibilitat_horaria`, `horari_lliure`, `reservable`
- Relacions: `ManyToMany` amb `horaris.FranjaHoraria`
- Propòsit: representar recursos del centre (portàtils, equips de vídeo, etc.).

#### `ReservaRecurs`
- Camps principals: `recurs`, `dia_reserva`, `hora_inici`, `hora_fi`, `hora`, `usuari`, `motiu`, `es_reserva_manual`
- Relacions: `ForeignKey` a `material.Recurs`, `horaris.FranjaHoraria`, `auth.User`
- Propòsit: reservar un recurs concret en un interval de temps.

---

### 2.15. `todo`

#### `ToDo`
- Camps principals: `propietari`, `data`, `tasca`, `informacio_adicional`, `estat`, `prioritat`, `enllac`
- Relacions: `ForeignKey` a `auth.User`
- Propòsit: gestió de tasques pendents del sistema o de l'usuari.

---

### 2.16. `baixes`

#### `Feina`
- Camps principals: `impartir`, `feina_a_fer`, `professor_fa_guardia`, `comentaris_per_al_professor_guardia`, `comentaris_professor_guardia`, `professor_darrera_modificacio`
- Relacions: `OneToOneField` a `presencia.Impartir`; `ForeignKey` a `usuaris.Professor`
- Propòsit: recollir la feina o tasca que han de fer els alumnes durant una guàrdia o absència.

---

### 2.17. `extPreinscripcio`

#### `Preinscripcio`
- Camps principals: dades personals i acadèmiques de l'alumnat en preinscripció (`nom`, `cognoms`, `ralc`, `codiestudis`, `curs`, `naixement`, `adreça`, `telefon`, `correu`, `centreassignat`, etc.)
- Propòsit: importar i gestionar sol·licituds de preinscripció.

#### `Nivell2Aula`
- Camps principals: `nivellgedac`, `nivellDjau`
- Relacions: `ForeignKey` a `alumnes.Nivell`
- Propòsit: mapar nivells del sistema extern i del model intern del centre.

---

### 2.18. `extSaga`, `extEsfera`, `extKronowin`, `extUntis`

#### `Agrupament` (`extUntis`)
- Camps principals: `grup_alumnes`, `grup_horari`
- Relacions: `ForeignKey` a `alumnes.Grup` als dos costats
- Propòsit: mapar agrupacions de grups externs amb grups del sistema intern.

#### `Grup2Aula` (`extSaga`, `extEsfera`, `extKronowin`)
- Camps principals: codi extern i connexió al grup intern (`Grup2Aula`)
- Relacions: `ForeignKey` a `alumnes.Grup`
- Propòsit: mapar grups de sistemes externs amb grups del DJAU.

#### `ParametreSaga`, `ParametreEsfera`, `ParametreKronowin`
- Camps principals: `nom_parametre`, `valor_parametre`
- Propòsit: emmagatzemar configuracions de sincronització amb cada sistema extern.

#### `Franja2Aula` (`extKronowin`)
- Camps principals: `franja_kronowin`, `franja_aula`
- Relacions: `ForeignKey` a `horaris.FranjaHoraria`
- Propòsit: mapar franges horàries de Kronowin amb les del sistema local.

---

## 3. Relacions més importants de l'esquema

### OneToOne
- `Responsable.user_associat` -> `auth.User`
- `DadesAddicionalsProfessor.professor` -> `usuaris.Professor`
- `SeguimentTutorial.alumne` -> `alumnes.Alumne`
- `Feina.impartir` -> `presencia.Impartir`

### ForeignKey
- `Nivell.taxes` -> `sortides.TipusQuota`
- `Curs.nivell` -> `alumnes.Nivell`
- `Grup.curs` -> `alumnes.Curs`
- `Alumne.grup` -> `alumnes.Grup`
- `Assignatura.curs` -> `alumnes.Curs`
- `Horari.assignatura` -> `assignatures.Assignatura`
- `Horari.professor` -> `usuaris.Professor`
- `Horari.grup` -> `alumnes.Grup`
- `Impartir.horari` -> `horaris.Horari`
- `ControlAssistencia.alumne` -> `alumnes.Alumne`
- `ControlAssistencia.impartir` -> `presencia.Impartir`
- `Incidencia` / `Sancio` / `Expulsio` -> alumnat, professors, franges i tipus de registre
- `Sortida.professor_que_proposa` -> `usuaris.Professor`
- `Matricula.curs` -> `alumnes.Curs`
- `Pagament.quota` / `Pagament.sortida` -> `sortides.Quota` / `sortides.Sortida`

### ManyToMany
- `Aula.disponibilitat_horaria` -> `horaris.FranjaHoraria`
- `Responsable.alumnes_associats` -> `alumnes.Alumne`
- `Sortida.professors_responsables` -> `usuaris.Professor`
- `Sortida.alumnes_convocats` -> `alumnes.Alumne`
- `Sortida.alumnes_que_no_vindran` -> `alumnes.Alumne`
- `Sortida.alumnes_justificacio` -> `alumnes.Alumne`
- `ItemQualitativa.nivells` -> `alumnes.Nivell`
- `AvaluacioQualitativa.grups` -> `alumnes.Grup`
- `Pagament.notificacions_familia` -> `usuaris.NotifUsuari`
- `Sancio.notificacions_familia` -> `usuaris.NotifUsuari`

---

## 4. Observacions sobre l'esquema

- El projecte fa servir una arquitectura amb models molt connectats entre si, amb una forta dependència de persones, grups, calendari i horaris.
- La majoria de les entitats estan dissenyades per ser utilitzades per un centre educatiu amb gestió d'alumnat, professorat, caps de setmana/activitats i comunicació amb famílies.
- La implementació de sincronització externa suggereix que part de la lògica d'importació manté mapatges entre dades del sistema extern i la base de dades del centre.
- Hi ha diversos models que són `proxy` o extensions simples per personalitzar llistats, ordenacions i filtres sense duplicar taules.

## 5. Models buits o no concretats

Els fitxers `models.py` següents no contenen models actius o estan buits:

- `aula/apps/BI/models.py`
- `demo/models.py`
- `aula/mblapp/models.py`
- `aula/utils/models.py`

## 6. Resum executiu

La base de dades del projecte s'articula al voltant d'aquestes entitats clau:

1. `Alumne` / `Grup` / `Curs` / `Nivell`
2. `Professor` / `Departament` / `Professional`
3. `Assignatura` / `Horari` / `Aula`
4. `Impartir` / `ControlAssistencia`
5. `Incidencia` / `Sancio` / `Expulsio`
6. `Matricula` / `Quota` / `Pagament`
7. `Sortida` / `Responsable` / `NotificaSortida`
8. `SeguimentTutorial` / `Actuacio` / `CartaAbsentisme`
9. `AvaluacioQualitativa` / `RespostaAvaluacioQualitativa`
10. `Missatge` / `Destinatari`

Aquest esborrany és útil com a mapa inicial de la base de dades del sistema i pot servir com a punt de partida per a una documentació més formal de l'esquema relacional o per generar diagrames ER.
