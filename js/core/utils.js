/**
 * Funções de apoio puras: não mexem na página e não guardam estado.
 */

/**
 * Lê um valor dentro de objetos aninhados usando um caminho com pontos.
 * Se algo no caminho não existir, devolve o valor padrão em vez de quebrar.
 *
 * @example readPath({ secoes: { sobre: { titulo: 'Sobre' } } }, 'secoes.sobre.titulo') // 'Sobre'
 * @example readPath({}, 'secoes.sobre.titulo', 'Sem título')                         // 'Sem título'
 */
export function readPath(object, path, defaultValue = '') {
  let current = object;
  for (const key of path.split('.')) {
    if (current === null || current === undefined) return defaultValue;
    current = current[key];
  }
  return current ?? defaultValue;
}

/**
 * Garante uma lista: se o valor não for um array (ex.: campo ausente no JSON), devolve [].
 * Também remove itens vazios (null, undefined, '').
 */
export function asArray(value) {
  return Array.isArray(value) ? value.filter(Boolean) : [];
}

/**
 * Preenche as {lacunas} de um texto com valores.
 *
 * @example fillTemplate('© {ano} {nome}', { ano: 2026, nome: 'Rafael' }) // '© 2026 Rafael'
 */
export function fillTemplate(template, values = {}) {
  return String(template).replace(/\{(\w+)\}/g, (_, key) => values[key] ?? '');
}

/**
 * Separa itens em grupos pelo valor de um campo, mantendo a ordem em que aparecem.
 * Itens sem o campo vão para o grupo '_'.
 *
 * @example
 *   groupByField([{ tipo: 'a' }, { tipo: 'b' }, { tipo: 'a' }], 'tipo')
 *   // Map { 'a' => [item1, item3], 'b' => [item2] }
 * @returns {Map<string, object[]>}
 */
export function groupByField(items, fieldName) {
  const groups = new Map();
  for (const item of items) {
    const groupName = item[fieldName] || '_';
    if (!groups.has(groupName)) groups.set(groupName, []);
    groups.get(groupName).push(item);
  }
  return groups;
}

/** Um link é externo se aponta para outro site ou para um arquivo PDF. */
export function isExternalUrl(url) {
  try {
    const parsedUrl = new URL(url, location.href);
    const isOtherSite = parsedUrl.origin !== location.origin;
    const isPdf = /\.pdf$/i.test(parsedUrl.pathname);
    return isOtherSite || isPdf;
  } catch {
    return false;
  }
}

/**
 * Converte uma data ISO em data curta, no idioma informado.
 *
 * @example formatDate('2025-03-27', 'pt-BR') // '27 de mar. de 2025'
 */
export function formatDate(isoDate, language) {
  // Meio-dia evita que o fuso horário faça a data "voltar" um dia.
  const date = new Date(`${isoDate}T12:00:00`);
  if (Number.isNaN(date.getTime())) return isoDate;

  const formatter = new Intl.DateTimeFormat(language || undefined, { day: 'numeric', month: 'short', year: 'numeric' });
  return formatter.format(date);
}
