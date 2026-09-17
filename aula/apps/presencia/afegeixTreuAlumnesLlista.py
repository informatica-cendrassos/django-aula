# This Python file uses the following encoding: utf-8

# threading
import traceback
from threading import Thread

from django.contrib.auth.models import Group

# Q
from django.db.models import Q

# models
from aula.apps.missatgeria.missatges_a_usuaris import (
    FI_PROCES_AFEGIR_ALUMNES,
    FI_PROCES_AFEGIR_ALUMNES_AMB_ERRORS,
    FI_PROCES_SINCRONITZAR_ALUMNES_RALC,
    FI_PROCES_SINCRONITZAR_ALUMNES_RALC_AMB_ERRORS,
    FI_PROCES_TREURE_ALUMNES,
    FI_PROCES_TREURE_ALUMNES_AMB_ERRORS,
    tipusMissatge,
)
from aula.apps.missatgeria.models import Missatge
from aula.apps.presencia.models import (
    ControlAssistencia,
    EstatControlAssistencia,
    Impartir,
)
from aula.apps.usuaris.models import User2Professor
from aula.utils.tools import unicode


class afegeixThread(Thread):
    def __init__(
        self, usuari, expandir=None, alumnes=None, impartir=None, matmulla=False
    ):
        Thread.__init__(self)
        self.expandir = expandir
        self.alumnes = alumnes
        self.impartir = impartir
        self.flagPrimerDiaFet = False
        self.usuari = usuari
        self.matmulla = matmulla

    def run(self):
        errors = []
        try:
            horaris_a_modificar = None

            if self.expandir:
                horaris_a_modificar = Q(
                    horari__assignatura=self.impartir.horari.assignatura
                )
                horaris_a_modificar &= Q(horari__grup=self.impartir.horari.grup)
                horaris_a_modificar &= Q(
                    horari__professor=self.impartir.horari.professor
                )
            else:
                horaris_a_modificar = Q(horari=self.impartir.horari)

            # from presencia.models import EstatControlAssistencia
            # estat_pendent, _  = EstatControlAssistencia.objects.get_or_create( codi_estat = u'-', defaults={ u'nom_estat' : u'-----' } )

            # afegeixo l'alumne sempre que no hi sigui:
            a_partir_avui = Q(dia_impartir__gte=self.impartir.dia_impartir)

            pks = (
                Impartir.objects.filter(horaris_a_modificar & a_partir_avui)
                .values_list("id", flat=True)
                .order_by("dia_impartir")
            )
            for pk in pks:
                i = Impartir.objects.get(pk=pk)
                alumnes_del_control = [
                    ca.alumne for ca in i.controlassistencia_set.all()
                ]
                for alumne in self.alumnes:
                    if alumne not in alumnes_del_control:
                        if self.matmulla:
                            # esborro l'alumne de les altres imparticions de la mateixa hora:
                            mateix_alumne = Q(alumne=alumne)
                            mateixa_hora = Q(impartir__horari__hora=i.horari.hora)
                            mateix_dia = Q(impartir__dia_impartir=i.dia_impartir)
                            mateixa_imparticio = Q(impartir=i)
                            ControlAssistencia.objects.filter(
                                mateix_alumne
                                & mateixa_hora
                                & mateix_dia
                                & ~mateixa_imparticio
                            ).delete()

                        # afegir
                        if (
                            alumne.data_baixa is None
                            or alumne.data_baixa > i.dia_impartir
                        ):
                            ca = ControlAssistencia(alumne=alumne, impartir=i)
                            # si ja han passar llista poso que falta:
                            falta = EstatControlAssistencia.objects.get(codi_estat="F")
                            if i.dia_passa_llista is not None:
                                ca.estat = falta
                                ca.professor = User2Professor(self.usuari)

                            ca.save()
                if i.pot_no_tenir_alumnes:
                    i.pot_no_tenir_alumnes = False
                    i.save()
                self.flagPrimerDiaFet = i.dia_impartir >= self.impartir.dia_impartir

        except Exception:
            errors.append(traceback.format_exc())

        finally:
            self.flagPrimerDiaFet = True
        missatge = FI_PROCES_AFEGIR_ALUMNES
        tipus_de_missatge = tipusMissatge(missatge)
        msg = Missatge(
            remitent=self.usuari,
            text_missatge=missatge.format(self.impartir.horari.assignatura),
            tipus_de_missatge=tipus_de_missatge,
        )
        importancia = "PI"

        if len(errors) > 0:
            missatge = FI_PROCES_AFEGIR_ALUMNES_AMB_ERRORS
            msg.afegeix_error(
                [
                    missatge.format(self.impartir),
                ]
            )
            msg.tipus_de_missatge = tipusMissatge(missatge)
            importancia = "VI"
            msg.save()
            administradors, _ = Group.objects.get_or_create(name="administradors")

            msgAdmins = Missatge(
                remitent=self.usuari, text_missatge=missatge.format(self.impartir)
            )
            msgAdmins.afegeix_error(errors)
            msgAdmins.save()
            msgAdmins.envia_a_grup(administradors, importancia)

            msg.envia_a_usuari(self.usuari, importancia)
        return errors

    def primerDiaFet(self):
        return self.flagPrimerDiaFet


# ---------------------------------------------------------------------------------------------------------------------------------


class treuThread(Thread):
    def __init__(
        self, expandir=None, alumnes=None, impartir=None, matmulla=False, usuari=None
    ):
        Thread.__init__(self)
        self.expandir = expandir
        self.alumnes = alumnes
        self.impartir = impartir
        self.flagPrimerDiaFet = False
        self.matmulla = matmulla
        self.usuari = usuari

    def run(self):
        errors = []
        try:
            horaris_a_modificar = Q(horari=self.impartir.horari)
            if self.expandir:
                horaris_a_modificar = Q(
                    horari__assignatura=self.impartir.horari.assignatura
                )
                horaris_a_modificar &= Q(horari__grup=self.impartir.horari.grup)
                horaris_a_modificar &= Q(
                    horari__professor=self.impartir.horari.professor
                )

            # trec els alumnes:
            a_partir_avui = Q(dia_impartir__gte=self.impartir.dia_impartir)

            pks = (
                Impartir.objects.filter(horaris_a_modificar & a_partir_avui)
                .values_list("id", flat=True)
                .order_by("dia_impartir")
            )
            for pk in pks:
                i = Impartir.objects.get(pk=pk)
                alumnes_a_esborrar = Q(alumne__in=self.alumnes)
                te_incidencies = Q(incidencia__isnull=False)
                te_expulsions = Q(expulsio__isnull=False)
                no_ha_passat_llista = Q(estat__isnull=True)
                if self.matmulla:
                    no_ha_passat_llista |= Q(estat__codi_estat="F")
                condicio = (
                    alumnes_a_esborrar
                    & ~te_incidencies
                    & ~te_expulsions
                    & no_ha_passat_llista
                )
                i.controlassistencia_set.filter(condicio).delete()

                self.flagPrimerDiaFet = i.dia_impartir >= self.impartir.dia_impartir

        except Exception as e:
            errors.append(unicode(e))

        finally:
            self.flagPrimerDiaFet = True

        missatge = FI_PROCES_TREURE_ALUMNES
        tipus_de_missatge = tipusMissatge(missatge)
        msg = Missatge(
            remitent=self.usuari,
            text_missatge=missatge.format(self.impartir.horari.assignatura),
            tipus_de_missatge=tipus_de_missatge,
        )
        importancia = "PI"

        if len(errors) > 0:
            msg.afegeix_error(errors)
            importancia = "VI"
            msg.save()
            administradors, _ = Group.objects.get_or_create(name="administradors")
            missatge = FI_PROCES_TREURE_ALUMNES_AMB_ERRORS
            tipus_de_missatge = tipusMissatge(missatge)
            msgAdmins = Missatge(
                remitent=self.usuari,
                text_missatge=missatge.format(self.impartir),
                tipus_de_missatge=tipus_de_missatge,
            )
            msgAdmins.afegeix_error(errors)
            msgAdmins.save()
            msgAdmins.envia_a_grup(administradors, importancia)

            msg.envia_a_usuari(self.usuari, importancia)

        return errors

    def primerDiaFet(self):
        return self.flagPrimerDiaFet


# ---------------------------------------------------------------------------------------------------------------------------------


class afegeixTreuByRalcThread(Thread):
    """Sincronitza la llista d'alumnes d'un horari amb una llista de RALC.

    Les dues fases es fan seguides per cada impartició perquè un alumne que
    s'ha de conservar o afegir no depengui d'un segon procés concurrent.
    """

    def __init__(self, usuari, impartir, alumnes):
        Thread.__init__(self)
        self.usuari = usuari
        self.impartir = impartir
        self.alumnes = list(alumnes)
        self.flagPrimerDiaFet = False

    def run(self):
        errors = []
        try:
            a_partir_avui = Q(dia_impartir__gte=self.impartir.dia_impartir)
            pks = (
                Impartir.objects.filter(Q(horari=self.impartir.horari) & a_partir_avui)
                .order_by("dia_impartir", "pk")
                .values_list("pk", flat=True)
            )
            alumnes_desitjats_pk = [alumne.pk for alumne in self.alumnes]

            for index, pk in enumerate(pks):
                imparticio = Impartir.objects.get(pk=pk)

                # Retirada forçada: només es poden treure entrades sense
                # incidència ni expulsió, i encara no passades o amb falta.
                condicio_treure = (
                    ~Q(alumne__in=alumnes_desitjats_pk)
                    & Q(incidencia__isnull=True)
                    & Q(expulsio__isnull=True)
                    & (Q(estat__isnull=True) | Q(estat__codi_estat="F"))
                )
                imparticio.controlassistencia_set.filter(condicio_treure).delete()

                alumnes_afegits = False
                for alumne in self.alumnes:
                    if ControlAssistencia.objects.filter(
                        alumne=alumne, impartir=imparticio
                    ).exists():
                        continue
                    if (
                        alumne.data_baixa is not None
                        and alumne.data_baixa <= imparticio.dia_impartir
                    ):
                        continue

                    control = ControlAssistencia(alumne=alumne, impartir=imparticio)
                    if imparticio.dia_passa_llista is not None:
                        control.estat = EstatControlAssistencia.objects.get(
                            codi_estat="F"
                        )
                        control.professor = User2Professor(self.usuari)
                    control.save()
                    alumnes_afegits = True

                if alumnes_afegits or imparticio.pot_no_tenir_alumnes:
                    imparticio.pot_no_tenir_alumnes = False
                    imparticio.save()

                # La vista pot tornar a passar llista quan la primera
                # impartició ja ha completat tant la retirada com l'afegit.
                if index == 0:
                    self.flagPrimerDiaFet = True

        except Exception:
            errors.append(traceback.format_exc())
        finally:
            # Evita que la vista quedi esperant indefinidament si el procés
            # falla abans d'arribar a la primera impartició.
            self.flagPrimerDiaFet = True

        missatge = FI_PROCES_SINCRONITZAR_ALUMNES_RALC
        msg = Missatge(
            remitent=self.usuari,
            text_missatge=missatge.format(self.impartir.horari.assignatura),
            tipus_de_missatge=tipusMissatge(missatge),
        )
        if errors:
            missatge_error = FI_PROCES_SINCRONITZAR_ALUMNES_RALC_AMB_ERRORS
            msg.afegeix_error([missatge_error.format(self.impartir)])
            msg.tipus_de_missatge = tipusMissatge(missatge_error)
            msg.save()

            administradors, _ = Group.objects.get_or_create(name="administradors")
            msg_admins = Missatge(
                remitent=self.usuari,
                text_missatge=missatge_error.format(self.impartir),
                tipus_de_missatge=tipusMissatge(missatge_error),
            )
            msg_admins.afegeix_error(errors)
            msg_admins.save()
            msg_admins.envia_a_grup(administradors, "VI")
            msg.envia_a_usuari(self.usuari, "VI")

        return errors

    def primerDiaFet(self):
        return self.flagPrimerDiaFet


# --------------------------------------------------------


class marcaSenseAlumnesThread(Thread):
    def __init__(
        self,
        expandir=None,
        impartir=None,
    ):
        Thread.__init__(self)
        self.expandir = expandir
        self.impartir = impartir
        self.flagPrimerDiaFet = False

    def run(self):
        errors = []
        try:
            horaris_a_modificar = Q(horari=self.impartir.horari)
            if self.expandir:
                horaris_a_modificar = Q(
                    horari__assignatura=self.impartir.horari.assignatura
                )
                horaris_a_modificar &= Q(horari__grup=self.impartir.horari.grup)
                horaris_a_modificar &= Q(
                    horari__professor=self.impartir.horari.professor
                )

            # trec els alumnes:
            a_partir_avui = Q(dia_impartir__gte=self.impartir.dia_impartir)

            pks = (
                Impartir.objects.filter(horaris_a_modificar & a_partir_avui)
                .values_list("id", flat=True)
                .order_by("dia_impartir")
            )
            for pk in pks:
                i = Impartir.objects.get(pk=pk)

                if not i.controlassistencia_set.exists():
                    i.pot_no_tenir_alumnes = True
                    i.save()

                self.flagPrimerDiaFet = i.dia_impartir >= self.impartir.dia_impartir

        except Exception as e:
            errors.append(unicode(e))

        finally:
            self.flagPrimerDiaFet = True

        return errors

    def primerDiaFet(self):
        return self.flagPrimerDiaFet
