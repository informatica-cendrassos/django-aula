from django.db.models import Q

from aula.apps.alumnes.models import Alumne


def alumnes_portal(professor):
    """Alumnes visibles a Tutoria / Portal per al professor efectiu."""
    if professor is None:
        return Alumne.objects.none()
    return Alumne.objects.filter(
        Q(grup__tutor__professor=professor)
        | Q(tutorindividualitzat__professor=professor)
    ).distinct()
