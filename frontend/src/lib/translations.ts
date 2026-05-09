/**
 * Diccionario de traducción para conceptos/áreas OpenAlex.
 * Cubre los ~100 conceptos más frecuentes en la BD UAT.
 * Los conceptos sin entrada se muestran en inglés original.
 */
export const CONCEPT_TRANSLATIONS: Record<string, string> = {
  // Ciencias básicas
  Biology: "Biología",
  Chemistry: "Química",
  Physics: "Física",
  Mathematics: "Matemáticas",
  Ecology: "Ecología",
  Genetics: "Genética",
  Biochemistry: "Bioquímica",
  "Organic chemistry": "Química orgánica",
  "Mathematical analysis": "Análisis matemático",
  "Quantum mechanics": "Mecánica cuántica",
  Geometry: "Geometría",
  Statistics: "Estadística",
  Microbiology: "Microbiología",
  Virology: "Virología",
  Immunology: "Inmunología",
  Paleontology: "Paleontología",
  Botany: "Botánica",
  Zoology: "Zoología",
  Neuroscience: "Neurociencia",

  // Medicina y salud
  Medicine: "Medicina",
  "Internal medicine": "Medicina interna",
  Pathology: "Patología",
  Surgery: "Cirugía",
  Psychiatry: "Psiquiatría",
  Gynecology: "Ginecología",
  Endocrinology: "Endocrinología",
  "Clinical psychology": "Psicología clínica",
  "Veterinary medicine": "Medicina veterinaria",
  Gerontology: "Gerontología",
  "Environmental health": "Salud ambiental",
  Disease: "Enfermedad",
  Pregnancy: "Embarazo",
  "Diabetes mellitus": "Diabetes mellitus",
  "Infectious disease (medical specialty)": "Enfermedades infecciosas",
  Chromatography: "Cromatografía",

  // Ciencias sociales y humanidades
  Humanities: "Humanidades",
  Philosophy: "Filosofía",
  "Political science": "Ciencias políticas",
  Psychology: "Psicología",
  Sociology: "Sociología",
  Economics: "Economía",
  Law: "Derecho",
  Demography: "Demografía",
  Linguistics: "Lingüística",
  Archaeology: "Arqueología",
  "Social psychology": "Psicología social",
  "Social science": "Ciencias sociales",
  "Developmental psychology": "Psicología del desarrollo",
  Epistemology: "Epistemología",
  "Welfare economics": "Economía del bienestar",
  Pedagogy: "Pedagogía",
  Marketing: "Mercadotecnia",
  Business: "Administración",
  Finance: "Finanzas",
  "Knowledge management": "Gestión del conocimiento",
  Politics: "Política",
  "PEST analysis": "Análisis PEST",

  // Tecnología e ingeniería
  "Computer science": "Ciencias de la computación",
  Engineering: "Ingeniería",
  "Artificial intelligence": "Inteligencia artificial",
  "Machine learning": "Aprendizaje automático",
  "Materials science": "Ciencia de materiales",
  "Mechanical engineering": "Ingeniería mecánica",
  "Electrical engineering": "Ingeniería eléctrica",
  Telecommunications: "Telecomunicaciones",
  "Programming language": "Lenguaje de programación",
  "Operating system": "Sistema operativo",
  "Process (computing)": "Proceso (computación)",
  Algorithm: "Algoritmo",
  Optics: "Óptica",
  Optoelectronics: "Optoelectrónica",
  "Composite material": "Material compuesto",
  Metallurgy: "Metalurgia",
  "Antenna (radio)": "Antena (radio)",

  // Ciencias de la tierra y medio ambiente
  Geography: "Geografía",
  "Environmental science": "Ciencias ambientales",
  Geology: "Geología",
  Cartography: "Cartografía",
  Forestry: "Silvicultura",

  // Ciencias agropecuarias y alimentarias
  "Food science": "Ciencia de los alimentos",
  Agronomy: "Agronomía",
  "Animal science": "Zootecnia",
  Horticulture: "Horticultura",
  Fishery: "Ciencias pesqueras",
  Fermentation: "Fermentación",

  // Arte, humanidades específicas
  Art: "Arte",

  // Biología especializada
  Parasitoid: "Parasitoide",
  Gene: "Gen",
  Bacteria: "Bacterias",
  Population: "Población",
  "Context (archaeology)": "Contexto arqueológico",
  "Fish <Actinopterygii>": "Peces (Actinopterygii)",
  Genus: "Género (taxonomía)",
  "Work (physics)": "Trabajo (física)",
  "World Wide Web": "World Wide Web",
  "Coronavirus disease 2019 (COVID-19)": "COVID-19",
};

/** Traduce un concepto al español; si no hay traducción devuelve el original. */
export function translateConcept(concept: string): string {
  return CONCEPT_TRANSLATIONS[concept] ?? concept;
}
