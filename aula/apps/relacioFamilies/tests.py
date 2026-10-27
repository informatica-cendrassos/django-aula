from datetime import date
from unittest.mock import patch

from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils.html import escape

from aula.apps.alumnes.models import Alumne, Curs, Grup, Nivell
from aula.apps.relacioFamilies.forms import CorreuAlumnesPortalForm
from aula.apps.relacioFamilies.permissions import alumnes_portal
from aula.apps.tutoria.models import Tutor, TutorIndividualitzat
from aula.apps.usuaris.models import User2Professor


class CorreuAlumnesPortalTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        professors = Group.objects.create(name="professors")
        cls.user = User.objects.create_user(username="tutor")
        cls.altre_user = User.objects.create_user(username="altre_tutor")
        cls.sense_tutoria = User.objects.create_user(username="sense_tutoria")
        for user in (cls.user, cls.altre_user, cls.sense_tutoria):
            user.groups.add(professors)
        cls.professor = User2Professor(cls.user)
        cls.altre_professor = User2Professor(cls.altre_user)
        nivell = Nivell.objects.create(nom_nivell="ESO")
        curs = Curs.objects.create(
            nivell=nivell, nom_curs="1", nom_curs_complert="1r ESO"
        )
        cls.grup = Grup.objects.create(curs=curs, nom_grup="A")
        cls.altre_grup = Grup.objects.create(curs=curs, nom_grup="B")
        Tutor.objects.create(professor=cls.professor, grup=cls.grup)
        Tutor.objects.create(professor=cls.altre_professor, grup=cls.altre_grup)
        cls.alumne = cls.crea_alumne("00123456789", cls.grup)
        cls.individual = cls.crea_alumne("98765432100", cls.altre_grup)
        cls.fora = cls.crea_alumne("11111111111", cls.altre_grup)
        TutorIndividualitzat.objects.create(
            professor=cls.professor, alumne=cls.individual
        )
        cls.url = reverse("tutoria__correu_alumnes_portal__per_idalu")

    @staticmethod
    def crea_alumne(ralc, grup):
        return Alumne.objects.create(
            ralc=ralc,
            grup=grup,
            nom="Alumne",
            cognoms=ralc,
            data_neixement=date(2010, 1, 1),
            correu="anterior@example.org",
            observacions="Conservar observacions",
            aruco_marker=Alumne.objects.count(),
        )

    def setUp(self):
        self.client.force_login(self.user)
        validacio_email = patch(
            "aula.apps.relacioFamilies.forms.testEmail",
            return_value=(0, "valid@example.org"),
        )
        self.validacio_email = validacio_email.start()
        self.addCleanup(validacio_email.stop)

    def test_menu_i_formulari(self):
        response = self.client.get(self.url)
        self.assertContains(response, "Correu alumnes portal x IDALU")
        self.assertContains(response, f'href="{self.url}"')
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.assertContains(response, 'name="dades"')
        self.assertFalse(response.context["form"].is_bound)

    def test_importa_excel_grup_i_individual_sense_modificar_altres_camps(self):
        abans = Alumne.objects.values().get(pk=self.alumne.pk)
        dades = (
            "IDALU (Ralc)\temail\r\n"
            f" {self.alumne.ralc} \t nou@example.org \r\n"
            "\t\r\n"
            f'"{self.individual.ralc}"\t"individual@example.org"\r\n'
        )
        response = self.client.post(self.url, {"dades": dades}, follow=True)
        self.assertRedirects(response, self.url)
        self.alumne.refresh_from_db()
        self.individual.refresh_from_db()
        self.fora.refresh_from_db()
        self.assertEqual(self.alumne.correu, "nou@example.org")
        self.assertEqual(self.individual.correu, "individual@example.org")
        self.assertEqual(self.fora.correu, "anterior@example.org")
        despres = Alumne.objects.values().get(pk=self.alumne.pk)
        abans.pop("correu")
        despres.pop("correu")
        self.assertEqual(abans, despres)
        self.validacio_email.assert_any_call("nou@example.org", False)
        self.assertContains(
            response, escape("S'ha desat el correu de 2 alumnes.")
        )

    def test_configuracio_individual_comparteix_els_permisos(self):
        for alumne, status in (
            (self.alumne, 200),
            (self.individual, 200),
            (self.fora, 404),
        ):
            with self.subTest(ralc=alumne.ralc):
                response = self.client.get(
                    reverse(
                        "tutoria__relacio_families___configura_connexio",
                        kwargs={"pk": alumne.pk},
                    )
                )
                self.assertEqual(response.status_code, status)

    def test_alumnes_visibles_son_els_mateixos_que_al_portal(self):
        TutorIndividualitzat.objects.create(
            professor=self.professor, alumne=self.alumne
        )
        self.assertSetEqual(
            set(alumnes_portal(self.professor).values_list("pk", flat=True)),
            {self.alumne.pk, self.individual.pk},
        )
        response = self.client.get(
            reverse("tutoria__relacio_families__dades_relacio_families")
        )
        self.assertContains(response, self.alumne.ralc)
        self.assertContains(response, self.individual.ralc)
        self.assertNotContains(response, self.fora.ralc)
        response = self.client.post(
            self.url, {"dades": f"{self.alumne.ralc}\tnou@example.org"}
        )
        self.assertRedirects(response, self.url)

    def test_fila_sense_permis_o_inexistent_impedeix_tots_els_canvis(self):
        for ralc in (self.fora.ralc, "inexistent"):
            with self.subTest(ralc=ralc):
                dades = (
                    f"{self.alumne.ralc}\tnou@example.org\n"
                    f"{ralc}\taltre@example.org"
                )
                response = self.client.post(self.url, {"dades": dades})
                self.assertContains(response, "Fila 2:")
                self.assertContains(response, "no trobat entre els alumnes")
                self.assertEqual(response.context["form"]["dades"].value(), dades)
                self.alumne.refresh_from_db()
                self.fora.refresh_from_db()
                self.assertEqual(self.alumne.correu, "anterior@example.org")
                self.assertEqual(self.fora.correu, "anterior@example.org")

    def test_rebutja_files_incorrectes_i_duplicades_sense_desar(self):
        files_incorrectes = [
            ("sense_tab", "dues columnes"),
            ("\tnou@example.org", "falta l'IDALU"),
            (f"{self.individual.ralc}\t", "email vàlid i no buit"),
            (f"{self.individual.ralc}\tincorrecte", "email vàlid i no buit"),
            (f"{self.individual.ralc}\ta@example.org\textra", "dues columnes"),
            (f"{self.individual.ralc}\t{'a' * 230}@example.org", "email vàlid"),
            (f"{self.alumne.ralc}\taltre@example.org", "repetit"),
            ('"cometes sense tancar', "format de les columnes incorrecte"),
        ]
        for fila, error in files_incorrectes:
            with self.subTest(fila=fila):
                dades = f"{self.alumne.ralc}\tnou@example.org\n{fila}"
                response = self.client.post(self.url, {"dades": dades})
                self.assertContains(response, "Fila 2:")
                self.assertContains(response, escape(error))
                self.alumne.refresh_from_db()
                self.assertEqual(self.alumne.correu, "anterior@example.org")

    def test_rebutja_entrada_buida_o_nomes_capcalera(self):
        for dades in ("", " \t\r\n", "IDALU (RALC)\temail\r\n"):
            with self.subTest(dades=dades):
                form = CorreuAlumnesPortalForm(self.professor, {"dades": dades})
                self.assertFalse(form.is_valid())
                self.assertIn("dades", form.errors)

    def test_rebutja_ralc_ambigu_dins_del_portal(self):
        self.crea_alumne(self.alumne.ralc, self.grup)
        response = self.client.post(
            self.url, {"dades": f"{self.alumne.ralc}\tnou@example.org"}
        )
        self.assertContains(response, escape("correspon a més d'un alumne"))
        self.alumne.refresh_from_db()
        self.assertEqual(self.alumne.correu, "anterior@example.org")

    def test_no_consulta_ni_modifica_coincidencies_fora_del_portal(self):
        duplicat_fora = self.crea_alumne(self.alumne.ralc, self.altre_grup)
        response = self.client.post(
            self.url, {"dades": f"{self.alumne.ralc}\tnou@example.org"}
        )
        self.assertRedirects(response, self.url)
        duplicat_fora.refresh_from_db()
        self.assertEqual(duplicat_fora.correu, "anterior@example.org")

    def test_mateixa_validacio_de_domini_que_el_portal(self):
        self.validacio_email.return_value = (-3, "nou@example.org")
        response = self.client.post(
            self.url, {"dades": f"{self.alumne.ralc}\tnou@example.org"}
        )
        self.assertContains(response, "adreça de correu o domini no vàlid")
        self.alumne.refresh_from_db()
        self.assertEqual(self.alumne.correu, "anterior@example.org")

    def test_tutor_nomes_individualitzat_pot_importar(self):
        Tutor.objects.filter(professor=self.professor).delete()
        response = self.client.post(
            self.url, {"dades": f"{self.individual.ralc}\tnou@example.org"}
        )
        self.assertRedirects(response, self.url)
        self.individual.refresh_from_db()
        self.assertEqual(self.individual.correu, "nou@example.org")

    def test_professor_sense_tutoria_no_pot_importar(self):
        self.client.force_login(self.sense_tutoria)
        response = self.client.post(
            self.url, {"dades": f"{self.alumne.ralc}\tnou@example.org"}
        )
        self.assertContains(response, "no trobat entre els alumnes")
        self.alumne.refresh_from_db()
        self.assertEqual(self.alumne.correu, "anterior@example.org")

    def test_l4_no_amplia_els_alumnes_del_portal(self):
        session = self.client.session
        session["l4"] = True
        session.save()
        response = self.client.post(
            self.url, {"dades": f"{self.fora.ralc}\tnou@example.org"}
        )
        self.assertContains(response, "no trobat entre els alumnes")
        self.fora.refresh_from_db()
        self.assertEqual(self.fora.correu, "anterior@example.org")

    def test_impersonacio_utilitza_els_alumnes_del_professor_efectiu(self):
        session = self.client.session
        session["impersonacio"] = self.altre_user.pk
        session["l4"] = True
        session.save()
        response = self.client.post(
            self.url, {"dades": f"{self.alumne.ralc}\tnou@example.org"}
        )
        self.assertContains(response, "no trobat entre els alumnes")
        response = self.client.post(
            self.url, {"dades": f"{self.fora.ralc}\tnou@example.org"}
        )
        self.assertRedirects(response, self.url)
        self.alumne.refresh_from_db()
        self.fora.refresh_from_db()
        self.assertEqual(self.alumne.correu, "anterior@example.org")
        self.assertEqual(self.fora.correu, "nou@example.org")

    def test_usuari_sense_rol_i_anonim_no_poden_importar(self):
        self.client.force_login(User.objects.create_user(username="sense_rol"))
        response = self.client.post(
            self.url, {"dades": f"{self.alumne.ralc}\tnou@example.org"}
        )
        self.assertEqual(response.status_code, 404)
        self.client.logout()
        response = self.client.post(
            self.url, {"dades": f"{self.alumne.ralc}\tnou@example.org"}
        )
        self.assertEqual(response.status_code, 302)
        self.alumne.refresh_from_db()
        self.assertEqual(self.alumne.correu, "anterior@example.org")

    def test_post_requereix_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        response = client.post(
            self.url, {"dades": f"{self.alumne.ralc}\tnou@example.org"}
        )
        self.assertEqual(response.status_code, 403)

    def test_error_en_desar_desfa_tot_el_lot(self):
        save = Alumne.save

        def falla_segon(alumne, *args, **kwargs):
            if alumne.pk == self.individual.pk:
                raise RuntimeError("Error en desar")
            return save(alumne, *args, **kwargs)

        with (
            patch.object(Alumne, "save", new=falla_segon),
            self.assertRaisesMessage(RuntimeError, "Error en desar"),
        ):
            self.client.post(
                self.url,
                {
                    "dades": f"{self.alumne.ralc}\tnou@example.org\n"
                    f"{self.individual.ralc}\tindividual@example.org"
                },
            )
        self.alumne.refresh_from_db()
        self.assertEqual(self.alumne.correu, "anterior@example.org")
