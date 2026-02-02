# student/templatetags/custom_filters.py
from django import template
import re

register = template.Library()


@register.filter(name='split')
def split(value, delimiter='|'):
    """Sépare une chaîne par un délimiteur"""
    if value:
        return [item.strip() for item in value.split(delimiter)]
    return []


@register.filter(name='get_item')
def get_item(value, key):
    """Extrait une valeur par clé depuis une chaîne formatée"""
    if not value:
        return ''

    # Normaliser la casse pour la recherche
    search_key = key.lower()
    value_lower = value.lower()

    # Chercher le motif: "clé: valeur"
    pattern = rf'{re.escape(search_key)}[:\s]+([^|]+)'
    match = re.search(pattern, value_lower)

    if match:
        # Retourner la valeur originale (avec la casse originale)
        start_idx = value_lower.find(search_key)
        if start_idx != -1:
            # Trouver le début de la valeur après la clé
            value_start = start_idx + len(search_key)
            # Avancer jusqu'au premier caractère non-espace et non-deux-points
            while value_start < len(value) and value[value_start] in ': \t':
                value_start += 1
            # Trouver la fin de la valeur (jusqu'au prochain '|' ou fin de chaîne)
            value_end = value.find('|', value_start)
            if value_end == -1:
                value_end = len(value)

            return value[value_start:value_end].strip()

    return ''


@register.filter(name='extract_ine')
def extract_ine(value):
    """Extrait spécifiquement l'INE"""
    return get_item(value, 'INE')


@register.filter(name='extract_telephone')
def extract_telephone(value):
    """Extrait spécifiquement le téléphone"""
    return get_item(value, 'Téléphone')


@register.filter(name='extract_adresse')
def extract_adresse(value):
    """Extrait spécifiquement l'adresse"""
    return get_item(value, 'Adresse')


@register.filter(name='format_address_display')
def format_address_display(value):
    """Formate l'adresse pour l'affichage (enlève les labels)"""
    if not value:
        return ''

    parts = []
    # Extraire chaque partie
    address = extract_adresse(value)
    ine = extract_ine(value)
    phone = extract_telephone(value)

    if address:
        parts.append(address)
    if ine:
        parts.append(f"INE: {ine}")
    if phone:
        parts.append(f"Tél: {phone}")

    return " | ".join(parts)