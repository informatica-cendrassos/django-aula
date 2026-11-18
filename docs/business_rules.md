# Regles de negoci i validació del projecte DJAU

Aquest document és una visió tècnica del domini funcional del sistema, construïda a partir de l'anàlisi dels models, formularis, vistes i business rules presents al repositori. El seu objectiu és resumir les regles de negoci crítiques, les condicions d'integritat del sistema i els patrons de validació que el software aplica abans de persistir canvis.

## 1. Arquitectura i patrons de disseny

El projecte utilitza Django en patró MVT amb una forta concentració de lògica de negoci fora dels models simples. La distribució funcional és la següent:

- `models.py` i `abstract_models.py`: definició de les entitats i atributs de domini.
- `forms.py`: validació de dades d'entrada i regles de consistència de formularis.
- `views.py`: orquestració del flux, control d'accés i gestió del guardat.
- `business_rules/*.py`: validació de regles de negoci complexa i branch logic.
- `signals` (`pre_save`, `post_save`, `pre_delete`, etc.): sincronització de dependències i efectes col·laterals.

El patró no és un model pur de domini anòmic ni de model-first estrictament; el projecte aplica validació en múltiples capes, amb una preferència clara per reforçar regles a la capa d'entrada i a la vista abans de fer `save()`.

## 2. Governança aplicada al repositori

Les instruccions del repositori imposen les següents restriccions operatives:

- no exposar secrets reals ni claus de producció;
- usar placeholders en documentació i exemples;
- no modificar settings de producció o migracions sense autorització explícita;
- respectar PEP 8 i el style guide del projecte;
- mantenir validació explícita de regles de negoci;
- generar proves en `tests.py` amb `django.test.TestCase`.

Aquestes regles no són meres pràctiques d'estil: condicionen la forma en què s'han de implementar canvis i validacions.

## 3. Domini funcional principal

### 3.1. Àrea acadèmica

L'eix central del sistema és la gestió de l'activitat acadèmica:

- `alumnes`: alumnes, nivells, cursos, grups, tutors i relacions de família.
- `assignatures`: matèries i classificació acadèmica.
- `horaris`: horaris, franjes horàries i dies lectius.
- `aules`: aules, disponibilitat i reserves.

Aquesta zona és la base dels fluxos de docència, presència i programació de l'horari.

### 3.2. Presència i assistència

La part de presència és la més densa en regles de negoci. Els models clau són:

- `Impartir`: una sessió de docència concreta (`dia_impartir`, `horari`, `professor_guardia`, `reserva`, etc.).
- `ControlAssistencia`: el registre d'assistència de cada alumne en una impartició.
- `EstatControlAssistencia`: classificació dels estats possibles de la falta/assistència.

La validació de presència es distribueix entre:

- `aula/apps/presencia/abstract_models.py`
- `aula/apps/presencia/models.py`
- `aula/apps/presencia/business_rules/controlassistencia.py`
- `aula/apps/presencia/forms.py`
- `aula/apps/presencia/views.py`

### 3.3. Incidències, sancions i expulsions

El sistema permet gestionar casos d'incidència i disciplina:

- faltes i retards;
- justificacions i cartes d'absentisme;
- sancions;
- expulsions;
- comunicació amb famílies o tutors.

Aquests models depenen de la consistència establerta en la sessió d'assistència i del rol del professor que actua.

### 3.4. Sortides i gestió administrativa

Les sortides tenen un flux d'estat explícit i regles de permisos molt concretes. El model de sortides fa validacions de:

- estats de revisió i gestió;
- permisos de direcció/coordinació;
- aprovació del Consell Escolar;
- codi de barres;
- informació de pagament;
- professorat organitzador i canvi de camps permesos.

La lògica es troba a `aula/apps/sortides/business_rules/sortida.py` i és un exemple de regles amb separació de responsabilitats per rol i per fase del procés.

### 3.5. Material i comunicació

El sistema també cobreix:

- reserva de material;
- gestió de comunicacions;
- avisos a usuaris i grups;
- relació amb famílies, professionals i directors.

## 4. Patró de validació i integritat del sistema

### 4.1. Validació en formulari

La capa `forms.py` és un punt central de validació. El projecte usa `clean()` i `clean_<field>()` per verificar que les dades compleixen el domini abans del guardat.

Exemples reals:

- `NetejaAulaForm.clean()` valida que si l'aula no està neta (`estat_neteja_aula != "N"`), cal indicar observacions.
- `disponibilitatAulaPerFranjaForm.clean()` valida la data i la franja respecte a la docència del dia.
- `reservaAulaForm.clean_hora()` valida que la franja reservada no estigui fora del rang de la docència real.

Aquest patró és important perquè elimina la dependència de la UI i reforça la consistència de les dades a la capa de presentació.

### 4.2. Validació en model

Els models criden a `clean()` o a funcions auxiliars de regla de negoci abans de persistir els canvis. A `aula/apps/presencia/models.py`:

- `Impartir.clean()` delega a `impartir_clean()`;
- `ControlAssistencia.clean()` delega a `controlAssistencia_clean()`;
- `EstatControlAssistencia.clean()` delega a `estatControlAssistencia_clean()`.

Aquesta pràctica és consistent al repositori i indica que el domini no queda reduït a un únic `ModelForm`; la regla de negoci és distribuïda en l'arquitectura del sistema.

### 4.3. Validació en vista

Les vistes afegeixen una segona capa d'assegurament abans de fer `save()`. Exemple a `aula/apps/presencia/views.py`:

- comprova els valors de `estat_neteja_aula` i `observacions_neteja`;
- valida que el valor sigui un codi acceptat del `ChoiceField`;
- afegeix errors a `NON_FIELD_ERRORS` si la lògica del formulari falla;
- bloqueja el `save()` si la validació de negoci no és correcta.

Aquesta sobrevalidació és essencial en un sistema que combina múltiples rols i fluxos amb traces d'auditoria.

### 4.4. Signals i efectes col·laterals

El repositori delega molta lògica en `pre_save`, `post_save`, `pre_delete` i `post_delete`. Això permet:

- sincronitzar reserves de classes;
- propagar canvis entre entitats relacionades;
- crear notificacions post-acció;
- eliminar o reassignar dependències.

Per exemple, a `aula/apps/presencia/business_rules/impartir.py` el `post_save` de `Impartir` gestiona la reserva associada i, si un professor passa llista, distribueix l'estat als altres horaris coincidents.

## 5. Regles de negoci crítiques per mòdul

### 5.1. Regles de neteja de l'aula

La classe `Impartir` defineix l'estat de neteja amb `ESTAT_NETEJA_AULA_CHOICES`:

```python
ESTAT_NETEJA_AULA_CHOICES = (
    ("N", "Aula neta"),
    ("A", "Aula acceptable"),
    ("B", "Aula bruta"),
)
```

Regla implementada:

```python
if estat and estat != "N":
    if not observacions or not observacions.strip():
        raise forms.ValidationError(
            "És obligatori indicar el motiu pel qual l'aula no està neta."
        )
```

La regla és important perquè no només descriu un estat de l'aula, sinó que obliga a registrar el motiu si aquesta no està en condicions adequades. La validació es reforça a la vista i al template per escurçar la possibilitat de dades inconsistents.

### 5.2. Regles d'assistència

Les regles observades a `controlassistencia.py` són molt precises:

- control de dates antigues amb `CUSTOM_PERIODE_MODIFICACIO_ASSISTENCIA`;
- permesos segons `User2Professor`, `User2Tutor` i identificació del professor de guàrdia;
- bloqueig de justificacions si el tutor ja ho ha fet;
- limitació de justificacions a tutors si `CUSTOM_NOMES_TUTOR_POT_JUSTIFICAR` està activat;
- no permetre una justificació si hi ha una carta d'absentisme activa;
- disparar incidències automàtiques si el retard configura la regla.

Aquesta part del sistema és un exemple de business logic defensiva, no només de form validation.

### 5.3. Regles d'horari i reserva d'aula

Les validacions de `aules/forms.py` imposen la regla següent:

- una data reservada ha d'estar dins el marge de disponibilitat;
- una franja ha d'estar dins el dia amb docència, no fora del rang curricular;
- la reserva no pot violar la franja lectiva real del dia.

Això evita que determinades entitats quedin amb una reserva impossible o fora del seu horari real.

### 5.4. Regles de sortides

Les sortides presenten una de les implementacions més completes de flux d'estat. La validació del domini compara l'instància actual amb la base de dades i aplica les regles de la següent manera:

- si una sortida està en estat `G` (gestionada), només Direcció pot modificar-la;
- si l'estat és `R` o `G`, només la coordinació o direcció poden alterar-la, excepte camps permitits pel professor organitzador;
- passar a `R` requereix una sortida prèviament proposada i, en alguns casos, aprovació del Consell Escolar;
- passar a `G` requereix permisos de direcció;
- codi de barres i informació de pagament estan restringits a rols concrets.

Aquesta és una de les parts més representatives del patró “regles per rol + doble validació + estat de flux”.

## 6. Model de permisos del sistema

El sistema fa servir grups d'usuari i un decorador comú per a l'accés:

```python
def group_required(groups=[]):
    def decorator(func):
        def inner_decorator(request, *args, **kwargs):
            for group in groups:
                try:
                    if Group.objects.get(name=group) in request.user.groups.all():
                        return func(request, *args, **kwargs)
                except Group.DoesNotExist:
                    raise Exception("{0} no existeix".format(group))
            raise Http404()
```

Grups observats al repositori:

- `professors`
- `direcció`
- `administradors`
- `consergeria`
- `professional`
- `sortides`
- `reservador`
- `psicopedagog`

L'arquitectura de permisos és funcional però també és fràgil si es modifica de manera inconsistente; no és un sistema RBAC formal, sinó un control basat en grups i decoradors a cada vista. Per això és crític conservar la semàntica dels noms de grup i evitar canvis de rol sense revisar el flux de cada vista.

## 7. Condicions obligatòries del sistema

Aquests són els condicionants que el sistema considera imprescindibles per no acceptar una operació:

### 7.1. Condicions temporals

- data fora del marge permès per reservar;
- intents de modificar assistències massa antigues;
- combinacions d'hora i dia no coherents amb la docència programada.

### 7.2. Condicions d'estat

- l'estat d'una sortida determina qui pot modificar-la;
- l'estat de neteja de l'aula condiciona la necessitat d'explicació;
- determinats canvis només són permesos si el nou estat no contradiu la regulació del flux.

### 7.3. Condicions de rol

- només l'usuari amb el rol adequat pot actuar sobre determinades dades;
- el professor tutor, el professor de guàrdia i el professor titular no són equivalents;
- la direcció i la coordinació tenen permisos especials sobre estats avançats i resolucions d'incidències.

### 7.4. Condicions de consistència

- no es permeten camps buits quan la regla de negoci exigeix detall;
- no es permeten modificacions fora del rang horari real;
- no es permeten canvis sobre entitats semànticament bloquejades per l'estat actual.

## 8. Patrons de desenvolupament que cal mantenir

Per conservar la coherència del sistema, un canvi nou ha de respectar els següents patrons:

1. validar a la capa del formulari i reforçar a la vista;
2. no confiar nominalment en la UI; validar també el backend;
3. mantenir l'estructura de permisos per grup en cada vista;
4. no saltar-se les regles d'estat d'una entitat; 
5. evitar fer `save()` sense `clean()` o sense control de `ValidationError`;
6. afegir tests reals de comportament per cada regla nova o canviada.

## 9. Observacions sobre tests i validació

El repositori exigeix proves amb Django `TestCase`, però l'entorn actual del treball ha mostrat que la suite no pot crear la base de proves per limitació de permisos del sistema de BD. Això no invalida la lògica observada al codi, però sí que impedeix la validació end-to-end del projecte en aquest entorn concret.

En termes pràctics, la validació efectiva del domini es realitza a través de:

- test unitaris de formulari;
- assertions sobre `clean()` i `ValidationError`;
- validació directa de la lògica de business rules;
- verificació de la integració de la vista en el flux de reacció.

## 10. Conclusió

DJAU està construït sobre un esquema de validació multicapa i regles de negoci en temps real. Les regles no es limiten a la presència; abasten horaris, reserves, assistència, incidències, sortides, tutela, comunicació i permisos d'usuari. En aquest model, la lògica de negoci és parteix de l'arquitectura del sistema i no una capa addicional opcional.

La neteja de l'aula és un exemple representatiu del patró general: una regla de domini concreta implementada en `Form`, revalidada en `View`, reforçada per `template` i condicionada per els permisos i les operacions del sistema.

Aquest document és un borrador tècnic de referència i pot ampliar-se a mesura que es revisin altres mòduls del projecte.
