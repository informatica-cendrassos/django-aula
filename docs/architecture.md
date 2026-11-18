# Arquitectura del projecte DJAU

Aquest document és un borrador tècnic de l'arquitectura del projecte Django. El seu objectiu és resumir la composició de carpetes, el patró MVT, l'ordres de configuració global, la gestió de rutes i les dependències externes que vertebren l'aplicació.

## 1. Visió general

DJAU és un sistema de gestió educativa implementat com a Django monolític modular. La lògica funcional no es concentra en una sola app, sinó que es distribueix en múltiples apps temàtiques agrupades sota `aula/apps/`, totes elles integrades en un mateix projecte Django (`aula`).

L'estructura té les característiques següents:

- arquitectura MVT (Model-View-Template) amb regles de negoci reforçades en formularis, vistes i business rules;
- fort acoblament funcional entre els diferents mòduls del centre educatiu (alumnat, horaris, incidències, matrícula, sortides, tutoria, etc.);
- configuració centralitzada en `aula/settings_dir/common.py` i overrides per entorn en `aula/settings.py`, `settings_dir/dev.py`, `settings_local.py`;
- enrutament global a `aula/urls.py` i enrutaments locals per app;
- templates i assets compartits a `aula/templates/` i `aula/site-css/`;
- integració amb serveis externs via apps com `extSaga`, `extEsfera`, `extKronowin`, `extUntis`, `mblapp`, etc.

---

## 2. Estructura de carpetes

La disposició principal del repositori és la següent:

```text
/opt/django/djau2025/
├── aula/
│   ├── apps/
│   │   ├── alumnes/
│   │   ├── assignatures/
│   │   ├── aules/
│   │   ├── avaluacioQualitativa/
│   │   ├── baixes/
│   │   ├── BI/
│   │   ├── extEsfera/
│   │   ├── extKronowin/
│   │   ├── extPreinscripcio/
│   │   ├── extSaga/
│   │   ├── extUntis/
│   │   ├── horaris/
│   │   ├── incidencies/
│   │   ├── material/
│   │   ├── matricula/
│   │   ├── missatgeria/
│   │   ├── presencia/
│   │   ├── presenciaSetmanal/
│   │   ├── relacioFamilies/
│   │   ├── sortides/
│   │   ├── todo/
│   │   ├── tutoria/
│   │   └── usuaris/
│   ├── mblapp/
│   ├── settings.py
│   ├── settings_dir/
│   │   ├── common.py
│   │   ├── demo.py
│   │   ├── dev.py
│   │   └── ...
│   ├── settings_local.py
│   ├── settings_local.sample
│   ├── site-css/
│   ├── templates/
│   ├── urls.py
│   ├── utils/
│   ├── wsgi.py
│   └── db.sqlite
├── customising/
├── demo/
├── docker/
├── docs/
├── scripts/
├── setup_djau/
├── manage.py
├── requirements.txt
├── README.md
├── tasks.py
├── tests.py
└── ...
```

### 2.1. `aula/`

És el paquet principal del projecte Django. Aquí s'hi concentra:

- configuració del projecte (`settings.py`, `settings_dir/*.py`);
- ubicació de rutes globals (`urls.py`);
- templates compartits (`templates/`);
- assets estàtics globals (`site-css/`);
- utils transversals (`utils/`);
- mòduls funcionals en `apps/`;
- API mòbil (`mblapp/`);
- configuració WSGI (`wsgi.py`).

### 2.2. `aula/apps/`

Cada carpeta representa un domini funcional. Els exemples principals són:

- `alumnes`: alumnat, grups, cursos, nivells
- `assignatures`: matèries i planificació acadèmica
- `horaris`: horaris i franges lectives
- `presencia`: assistència i impartició
- `incidencies`: sancions, expulsions i incidències
- `sortides`: excursions, pagaments i coordinació
- `tutoria`: seguiment tutorial i cartes d'absentisme
- `matricula`: matrícula i documents
- `relacioFamilies`: relació amb famílies i comunicació
- `usuaris`: usuaris, rols i perfils
- `aules` i `material`: reserves d'espais i recursos
- `extSaga`, `extEsfera`, `extKronowin`, `extUntis`: integració amb sistemes externs

### 2.3. `customising/` i `demo/`

- `customising/` serveix per personalitzar templates, URLs i termes de l'entorn concret.
- `demo/` aporta una instància de demostració amb els seus propis templates i helpers.

### 2.4. `docs/`

La documentació funcional i tècnica del projecte es concentra aquí. En aquesta carpeta hi ha documents de base de dades, regles de negoci i, en aquest cas, també la documentació d'arquitectura.

---

## 3. Configuració global i entorns

La configuració del projecte no es troba en un sol fitxer. Té una jerarquia clara:

### 3.1. `aula/settings_dir/common.py`

És la base del projecte. Defineix:

- `LANGUAGE_CODE = "ca"` i localització catalana;
- `TIME_ZONE = "Europe/Madrid"`;
- `ROOT_URLCONF = "aula.urls"`;
- `WSGI_APPLICATION = "aula.wsgi.application"`;
- `INSTALLED_APPS_DJANGO` i `INSTALLED_APPS_AULA`;
- `MIDDLEWARE` amb middleware de seguretat, sessió, auth, CSRF i personalitzat;
- `TEMPLATES` amb `filesystem.Loader` i `app_directories.Loader`;
- `STATICFILES_DIRS` i `STATIC_URL`;
- `REST_FRAMEWORK` i JWT;
- `LOGGING` i `PRIVATE_STORAGE_AUTH_FUNCTION`.

### 3.2. `aula/settings.py`

És la capa d'override per personalització funcional del sistema. Importa la base comuna i, si no hi ha `settings_local.py`, carrega la configuració de `settings_dir/demo.py`.

Aquesta configuració define moltes variables del domini educatiu del centre, com ara:

- comportament d'assistència i incidències;
- permisos de matrícula o sortides;
- temporitzacions de timeout;
- customització de grups, nivells i tipus d'incidència;
- paràmetres de pagament i comunicació.

### 3.3. `aula/settings_dir/dev.py`

És una configuració d'entorn de desenvolupament. Aquí es defineixen:

- base de dades configurable amb variables d'entorn;
- activació de `demo` com a app extra si cal;
- `MIDDLEWARE += [...]` per extensió del stack;
- configuració de depuració i e-mail de consola.

### 3.4. `aula/settings_local.py`

És la configuració local real de l'entorn del centre. Aquesta capa sol incloure:

- connexió a base de dades real;
- credencials i URLs locals;
- paràmetres de producció o preproducció;
- personalitzacions del sistema per centre.

> La configuració local és específica i no s'ha d'usar com a referència genèrica; és una sobreescriptura de la base del projecte.

---

## 4. Apps registrades i partició funcional

La llista de `INSTALLED_APPS_AULA` mostra la naturalesa de la solució: es tracta d'un monòlit modular orientat al domini educatiu.

### 4.1. Apps base de Django

```
- django.contrib.admin
- django.contrib.auth
- django.contrib.contenttypes
- django.contrib.sessions
- django.contrib.messages
- django.contrib.staticfiles
- django.contrib.sites
- django_extensions
- django_tables2
- django_select2
- django.contrib.humanize
- formtools
- django.forms
- rest_framework
- rest_framework_simplejwt
- django_gsuite_email
- crispy_forms
- crispy_bootstrap3
```

### 4.2. Apps funcionals del projecte

```
- aula.apps.missatgeria
- aula.apps.alumnes
- aula.apps.assignatures
- aula.apps.horaris
- aula.apps.presencia
- aula.apps.incidencies
- aula.apps.tutoria
- aula.apps.extKronowin
- aula.apps.extSaga
- aula.apps.extEsfera
- aula.apps.avaluacioQualitativa
- aula.apps.todo
- aula.apps.usuaris
- aula.apps.relacioFamilies
- aula.apps.sortides
- aula.apps.baixes
- aula.apps.BI
- aula.apps.aules
- aula.apps.material
- aula.utils
- aula.apps.presenciaSetmanal
- aula.apps.extUntis
- aula.apps.matricula
- aula.apps.extPreinscripcio
- aula.mblapp
```

Aquesta estructura és clau perquè la solució no és només una app de gestió genèrica: és una col·lecció d'escenaris educatius que comparteixen bases de dades, autenticació i fluxos compartits.

---

## 5. Rutes globals i enrutament per app

El rutes globals estan a `aula/urls.py` i actuen com a concentrador de flux d'entrada HTTP.

### 5.1. Patró de rutes principals

Les rutes globals inclouen:

- JWT: `api-token-auth`, `api-token-refresh`, `api-token-verify`
- manteniment: `keepalive`, `menu`, `logout`
- entorns funcionals:
  - `/alumnes/`
  - `/presencia/`
  - `/incidencies/`
  - `/usuaris/`
  - `/tutoria/`
  - `/sortides/`
  - `/matricula/`
  - `/aules/`
  - `/recursos/`
  - `/open/` per relació amb famílies
  - `/api/token/` per l'API mòbil
- admin: `/admin/`
- estàtics: `/site-css/...`
- media privada: `private-media/`

Això fa que el projecte segueixi un model de “frontcontroller de Django” i permet una modularització per domini sense perdre un punt d'entrada únic.

### 5.2. Enrutament local per app

Cada app té el seu propi `urls.py` amb `urlpatterns` que encapsulen les vistes del mòdul. Exemple de patró:

- `aula/apps/presencia/urls.py`
- `aula/apps/aules/urls.py`
- `aula/apps/material/urls.py`
- `aula/apps/matricula/urls.py`

Això porta a una arquitectura “monolític modular”: un projecte únic, però amb responsabilitat de routing per domini.

---

## 6. Flux MVT de peticions

El flux de petició segueix el patró clàssic de Django.

### 6.1. Seqüència típica

1. El navegador o client fa una petició HTTP a una URL.
2. `aula/urls.py` intercepta la ruta i redirigeix a una app concreta amb `include(...)`.
3. La app resol la ruta mitjançant `urls.py` de l'app.
4. La vista (funció o classe) rep la `request` i decideix quina lògica aplicar.
5. La vista consulta models (
   `Model.objects.filter(...)`, `get(...)`, etc.) i puede crear o validar formularis.
6. Si cal, la vista usa `Form` o `ModelForm` per validar l'entrada.
7. El resultat es renderitza mitjançant un template.
8. La resposta es retorna al client en HTML, JSON o redirect.

### 6.2. Exemple de flux

Un cas típic seria la preinscripció, la matrículació o la passació de llista:

- URL `/presencia/...` -> `aula.apps.presencia.urls`
- vista: `passaLlista`, `mostraImpartir`, etc.
- model: `Impartir`, `ControlAssistencia`
- formulari: `NetejaAulaForm`, `ModelForm` o formularis personalitzats
- template: `passaLlista.html` o una plantilla de llista
- resposta: HTML amb estat, errors de validació o redirecció

Aquest patró és la base del sistema i explica per què les regles de negoci es reparteixen entre model, formulari, vista i templates.

### 6.3. Vista, formulari i model com a capes de validació

Aquesta aplicació no depèn d'una única validació central. Les regles es distribueixen entre:

- `models.py`: estructura i dades
- `forms.py`: validació d'entrada i `clean()`
- `views.py`: orquestració del flux, autenticació, permisos i persistència
- `business_rules/*.py`: lògica específica de negoci complexa
- `templates/*`: condicionament de la interfície i feedback per a l'usuari

Això és molt important per entendre la lògica del repositori: la validació no és “invisible”, sinó que apareix en diferents capes.

---

## 7. Patró de validació i regles de negoci

El sistema aplica una estratègia de validació multicapa i defensiva:

### 7.1. Validació a nivell de model

Els models defineixen l'estructura del domini, però no sempre contenen tota la validació funcional. Normalment hi ha `clean()` o helpers especialitzats.

### 7.2. Validació a nivell de formulari

La validació de camp es fa en `forms.py`. És bastant habitual veure:

- `clean()`
- `clean_<field>()`
- `ValidationError` explícits
- control d'estats i observacions obligatòries

### 7.3. Validació a nivell de vista

Les vistes reforcen la validació abans de persistir. Aquest patró és recurrent i es fa servir per evitar que la capa UI o el client enviï dades inconsistents.

### 7.4. Business rules i orchestració

Les apps disposen de carpetes `business_rules/` o `rules` on hi ha la lògica de negoci més específica, sovint relacionada amb:

- assistència;
- incidències i sancions;
- sortides i pagaments;
- tutoria i absentisme;
- sincronització amb sistemes externs.

Aquest és un dels punts més rellevants de l’arquitectura: el domini no queda reduït a la capa ORM; es dispersa dins de regles de negoci explícites.

---

## 8. Middleware i seguretat transversal

El projecte define middleware propi a `aula/utils/middleware.py`.

### 8.1. `MultipleProxyMiddleware`

Normalitza els headers de proxy (`X-Forwarded-*`) perquè el sistema no interpreti una cadena de IPs o hosts amb càrrega pesada.

### 8.2. `NoCacheMiddleware`

Afegeix headers de cache invalidation per evitar que es reutilitzin respostes potenciament obsoletes.

### 8.3. `timeOutMiddleware`

Controla el timeout de sessió de l'usuari i tanca la sessió si l'usuari supera el temps d'inactivitat permes. Aquest middleware és una peça de control d'usuari molt rellevant en un sistema acadèmic amb grups i permisos.

### 8.4. `IncludeLoginInErrors`

Enriqueix les exceptions amb dades de l'usuari autenticat per facilitar la diagnosi d'errors i la depuració.

### 8.5. Middleware de Django integrat

La configuració comuna inclou també:

- `SecurityMiddleware`
- `SessionMiddleware`
- `CommonMiddleware`
- `CsrfViewMiddleware`
- `AuthenticationMiddleware`
- `MessageMiddleware`
- `ClickjackingMiddleware`

Això implica que el projecte està pensat per un entorn web corporatiu, amb sessions, auth i protecció de CSRF, més enllà del simple CRUD.

---

## 9. Templates i assets estàtics

### 9.1. Templates

Els templates es troben a:

- `aula/templates/`
- `customising/templates/` (si hi ha personalització local)
- alguns apps tenen templates propis dins d'ells

La configuració de `TEMPLATES` indica que el sistema usa:

- `filesystem.Loader` per carregar templates des del sistema de fitxers;
- `app_directories.Loader` per carregar templates de cada app;
- context processors per auth, request, messages i dades bàsiques.

### 9.2. Static files

Els assets estàtics es troben a:

- `aula/site-css/`
- subcarpetes de cada app si n'hi ha `static/`
- `customising/` per assets personalitzats

La configuració `STATICFILES_DIRS` i `STATICFILES_FINDERS` garanteix que Django pugui servir assets locals i de les apps.

### 9.3. Servei d'estàtics i media

Els fitxers estàtics de l'aplicació poden ser servits amb `site-css/...` i es configuren amb l'URL `/site-css/`. La media privada es gestiona amb `private_storage`, cosa que indica un model d'uploads amb accés restringit i no purament públic.

---

## 10. Dependències tècniques i integracions

El projecte té un stack de dependències molt complet. La llista de `requirements.txt` mostra un ecosistema orientat a gestió escolar i integració web.

### 10.1. Dependències principals

- Django (versió restringida per rang de compatibilitat)
- django-extensions
- django-environ
- django-tables2
- django-select2
- django-crispy-forms
- djangorestframework
- djangorestframework-simplejwt
- django-private-storage
- django-formtools
- Pillow
- lxml
- selenium
- psycopg2 / psycopg
- openpyxl / XlsxWriter / python-barcode
- matplotlib / opencv-contrib-python

### 10.2. Integracions de negoci i sistema

L'aplicació té integracions específiques amb fluxos acadèmics i sistemes externs:

- `extSaga`
- `extEsfera`
- `extKronowin`
- `extUntis`
- `mblapp` (API per aplicació mòbil)
- `django_gsuite_email`
- private media / documents vinculats a matrícula i relació amb famílies

Això converteix el sistema en una plataforma de gestió escolar amb múltiples fronts d'entrada (web, mòbil, sincronitzacions, exports i integracions).

---

## 11. Arquitectura tècnica general

### 11.1. Model arquitectònic

DJAU es pot descriure com un monolític modular Django amb:

- una base de dades central;
- múltiples apps funcionals;
- un sistema de permisos basat en grups d'usuari;
- templates i serveis de presentació web;
- API REST per integració externa;
- lògica de negoci repartida entre models, forms i business rules.

### 11.2. Acoblament funcional

La part més important de l'arquitectura és el fort acoblament funcional entre entitats:

- alumnat ↔ grups ↔ cursos ↔ nivells
- professorat ↔ horaris ↔ presència ↔ incidències
- sortides ↔ pagaments ↔ família
- matrícula ↔ documents ↔ quota
- tutoria ↔ absentisme ↔ incidències

Això vol dir que l'arquitectura de la base de dades és fonamental i que el sistema és més “de domini” que “de CRUD genèric”.

### 11.3. Característiques de disseny percebudes

Des del punt de vista tècnic, el projecte mostra les següents característiques:

- orientació a cas d'ús educatius molt concrets;
- fort ús d'override de configuració per entorn;
- estructuració funcional per àrees del centre;
- dependència d'operacions de calendari, permisos i àmbits;
- validació distribuïda, no centralitzada;
- combinació de web tradicional + API + sincronitzacions externes.

---

## 12. Conclusió

La solució DJAU és un projectes Django monolític però fortament modularitzat per domini. La seva arquitectura es basa en una combinació de:

- project root (`aula/`) com a contenedor principal;
- apps temàtiques (`aula/apps/*`) com a unitats de funcionalitat;
- capes de validació distribuïdes entre models, formularis i vistes;
- middleware transversals de sessió, timeout i proxy;
- templates i assets compartits;
- configuració per entorn i personalització local;
- integració de serveis externs i API REST.

Aquesta estructura és coherent amb un sistema escolar complex i amb moltes regles de negoci específiques, on el model de domini i el flux de permisos són tan importants com l'eina técnica en si mateixa.
