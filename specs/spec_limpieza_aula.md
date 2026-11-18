# Especificació Tècnica: Camp Obligatori d'Observacions per Neteja d'Aula

## 1. Objectiu
Permetre que el professorat enregistri la neteja de l'aula en passar llista i forçar la introducció d'observacions explicatives únicament si s'indica que l'aula no està neta.

## 2. Requisits Funcionals i d'UI
- **Camp de Neteja**: Camp booleà o selector en el formulari d'assistència per indicar si l'aula està neta (`aula_neta` / `neta`).
- **Camp d'Observacions**: Camp de text (`observacions_neteja`).
- **Lògica de Validació (Backend)**: 
  - Si `aula_neta` és `True` (Neta), `observacions_neteja` és opcional.
  - Si `aula_neta` és `False` (No neta), `observacions_neteja` passa a ser **estrictament obligatori** i no pot estar buit ni contenir només espais en blanc.
- **Comportament en Frontend**: Interacció dinàmica (JavaScript) per mostrar o ocultar/marcar com a `required` el camp d'observacions segons el valor del selector.

## 3. Modificacions Arquitectòniques a Django
- **`models.py` / `forms.py`**:
  - Afegir o verificar els camps a l'entitat corresponent (ex. `RegistreAssistencia` o `ControlAula`).
  - Implementar la validació personalitzada en el mètode `clean()` del `ModelForm` o del `Model`:
    ```python
    def clean(self):
        cleaned_data = super().clean()
        aula_neta = cleaned_data.get('aula_neta')
        observacions = cleaned_data.get('observacions_neteja')

        if aula_neta is False and not (observacions and observacions.strip()):
            self.add_error('observacions_neteja', "És obligatori indicar el motiu pel qual l'aula no està neta.")
    ```
- **`views.py`**: Assegurar que processa correctament la validació de formularis mitjançant `form.is_valid()`.
- **`templates/.../passar_llista.html`**: Actualitzar la plantilla HTML amb el renderitzat del nou camp i el script dinàmic per a la interfície.

## 4. Requisits de Proves (Tests)
Crear o ampliar proves a `tests.py` (`TestCase` de Django) que verifiquin:
1. Desat amb èxit amb `aula_neta=True` i observacions buides.
2. Error de validació amb `aula_neta=False` i observacions buides.
3. Desat amb èxit amb `aula_neta=False` i observacions omplertes. 
