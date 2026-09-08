"""Versioned, source-neutral tender classification rules.

The public sources do not expose competitionline's taxonomy.  These rules are
our transparent interpretation of CPV codes and German notice text.
"""
from collections.abc import Iterable

TAXONOMY_VERSION = "office-taxonomy-v1"

SERVICE_GROUPS = (
    ("object_planning", "Objektplanung", (
        ("construction_supervision", "Bauleitung / Objektüberwachung", ("7154",), ("bauleitung", "objektüberwachung", "bauüberwachung")),
        ("general_planning", "Generalplanerleistung", ("7124",), ("generalplan", "generalplaner")),
        ("open_space_planning", "Objektplanung Freianlagen", ("7142",), ("freianlagen", "freiraumplanung")),
        ("building_planning", "Objektplanung Gebäude", ("7122",), ("objektplanung gebäude", "gebäudeplanung", "architekturleistung")),
        ("civil_engineering", "Objektplanung Ingenieurbauwerke", ("7132",), ("ingenieurbauwerk", "brückenplanung")),
        ("interior_planning", "Objektplanung Innenräume", ("7122",), ("innenraum", "innenarchitektur")),
        ("supply_disposal_planning", "Objektplanung Ver-/Entsorgung", (), ("ver- und entsorgung", "entsorgungsanlage")),
        ("transport_planning", "Objektplanung Verkehrsanlagen", ("7132",), ("verkehrsanlage", "straßenplanung")),
        ("heritage", "Denkmalschutz", (), ("denkmalschutz", "denkmalpflege")),
        ("scenography", "Szenografie", (), ("szenografie",)),
    )),
    ("specialist_planning", "Fachplanung", (
        ("structural", "Tragwerksplanung", ("71327",), ("tragwerksplanung", "statik")),
        ("fire_protection", "Brandschutz", (), ("brandschutz",)),
        ("energy", "Energieplanung / -beratung", ("71314",), ("energieplanung", "energieberatung", "energieeffizienz")),
        ("facade", "Fassadenplanung", (), ("fassadenplanung", "fassade", "gebäudehülle")),
        ("emission_control", "Immissionsschutz", (), ("immissionsschutz",)),
        ("lighting", "Lichtplanung", (), ("lichtplanung",)),
        ("technical_equipment", "Technische Ausrüstung", ("71315",), ("technische ausrüstung", "tga")),
    )),
    ("consulting", "Beratungsleistungen", (
        ("contaminated_sites", "Altlastensanierung", (), ("altlast",)),
        ("geotechnics", "Bodenmechanik, Erd-/Grundbau", ("71332",), ("bodenmechanik", "baugrund", "grundbau")),
        ("acoustics", "Schallschutz, Raumakustik", (), ("schallschutz", "raumakustik")),
        ("safety", "Sicherheits-/Gesundheitsschutz", (), ("sicherheits", "gesundheitsschutz", "sigeko")),
        ("studies", "Studien, Gutachten", (), ("gutachten", "studie", "machbarkeits")),
        ("thermal_physics", "Thermische Bauphysik", (), ("bauphysik", "wärmeschutz")),
        ("environmental_impact", "Umweltverträglichkeitsstudie", (), ("umweltverträglichkeits",)),
        ("surveying", "Vermessung", ("71355",), ("vermessung",)),
    )),
    ("project_management", "Projekt- und Objektmanagement", (
        ("general_consulting", "Allgemeine Beratungsleistungen", ("7153",), ("beratungsleistung",)),
        ("procurement", "Ausschreibung, Vergabe", (), ("vergab", "ausschreibung")),
        ("facility_management", "Facility Management", (), ("facility management",)),
        ("monitoring", "Kontrolle, Monitoring", (), ("monitoring", "kontrolle")),
        ("cost_management", "Kostenmanagement", (), ("kostenmanagement", "kostensteuerung")),
        ("logistics_planning", "Logistikplanung", (), ("logistikplanung",)),
        ("project_control", "Projektsteuerung", (), ("projektsteuerung",)),
        ("competition_support", "Wettbewerbsbetreuung", (), ("wettbewerbsbetreuung",)),
    )),
    ("spatial_planning", "Flächenplanung", (
        ("urban_planning", "Stadt-/Gebietsplanung", ("7141",), ("stadtplanung", "gebietsplanung")),
        ("landscape_planning", "Landschaftsplanung", ("7142",), ("landschaftsplanung",)),
        ("land_use_planning", "Bauleitplanung", (), ("bauleitplanung", "flächennutzungsplan", "bebauungsplan")),
    )),
    ("other", "Andere", (
        ("bim", "BIM", (), ("building information modeling", " bim")),
        ("construction_work", "Bauleistung", ("45",), ("bauleistung",)),
        ("operation", "Betrieb", (), ("betrieb",)),
        ("documentation", "Dokumentation", (), ("dokumentation",)),
        ("financing", "Finanzierung", (), ("finanzierung",)),
        ("research", "Forschung, Entwicklung", (), ("forschung", "entwicklung")),
        ("photography", "Fotografie", (), ("fotografie",)),
        ("general_contractor", "Generalunternehmerleistung", (), ("generalunternehmer",)),
        ("art", "Kunst", (), ("kunst am bau",)),
        ("delivery", "Lieferung", ("3",), ("lieferung",)),
        ("visualization", "Visualisierung, Modellbau", (), ("visualisierung", "modellbau")),
    )),
)

OBJECT_TYPES = {
    "existing": ("Bauen im Bestand", ("bestand", "sanierung", "instandsetzung", "modernisierung", "umbau", "erweiterung", "revitalisierung", "denkmalschutz", "umnutzung", "fassade")),
    "new_build": ("Neubau", ("neubau", "ersatzneubau", "neuerrichtung")),
}

CORE_SERVICE_CODES = {"building_planning", "general_planning", "construction_supervision", "interior_planning", "facade", "energy", "heritage", "thermal_physics"}


def classify(title: str | None, description: str | None, cpv_codes: Iterable[str] | None) -> tuple[list[str], list[str], dict]:
    text = f"{title or ''} {description or ''}".lower()
    cpvs = tuple(cpv_codes or ())
    services: list[str] = []
    reasons: dict[str, list[str]] = {}
    for group_code, _label, leaves in SERVICE_GROUPS:
        for code, label, prefixes, signals in leaves:
            hits = [f"CPV {cpv}" for cpv in cpvs if cpv.startswith(prefixes)] if prefixes else []
            hits += [f"Text: {signal}" for signal in signals if signal in text]
            if hits:
                services.append(code)
                reasons[code] = hits
    existing = [signal for signal in OBJECT_TYPES["existing"][1] if signal in text]
    new_build = [signal for signal in OBJECT_TYPES["new_build"][1] if signal in text]
    if existing and new_build:
        objects = ["mixed"]
        reasons["mixed"] = [f"Text: {item}" for item in existing + new_build]
    elif existing:
        objects = ["existing"]
        reasons["existing"] = [f"Text: {item}" for item in existing]
    elif new_build:
        objects = ["new_build"]
        reasons["new_build"] = [f"Text: {item}" for item in new_build]
    else:
        objects = ["mixed"]
        reasons["mixed"] = ["Kein eindeutiges Objektart-Signal"]
    return sorted(set(services)), objects, reasons


def taxonomy_for_template() -> list[dict]:
    return [{"code": code, "label": label, "children": [{"code": leaf[0], "label": leaf[1]} for leaf in leaves]} for code, label, leaves in SERVICE_GROUPS]


def service_labels() -> dict[str, str]:
    return {leaf[0]: leaf[1] for _group, _label, leaves in SERVICE_GROUPS for leaf in leaves}
