/**
 * MediumService — busca os artigos mais recentes do Medium e os converte para
 * o mesmo formato de data.escritos.itens: { titulo, data, minutos, resumo, url }.
 *
 * Por que passar por um conversor (rss2json)?
 *   O feed RSS do Medium não permite ser lido por outros sites (não envia
 *   cabeçalhos CORS), então o navegador bloqueia a leitura direta. O rss2json.com
 *   busca o feed e devolve em JSON, com a leitura liberada.
 *
 * Por que juntar com o data.json (mergeWithSaved)?
 *   O feed traz só os ~10 artigos mais recentes. A lista salva garante que os
 *   antigos continuem aparecendo.
 */

/** Tamanho do resumo automático: junta parágrafos até MIN caracteres e corta em MAX. */
const SUMMARY_MIN_LENGTH = 120;
const SUMMARY_MAX_LENGTH = 220;

export class MediumService {
  /**
   * @param {object} settings  data.escritos.fonte
   * @param {string} settings.feed               Endereço do feed RSS do Medium.
   * @param {string} settings.proxy              Endereço do conversor RSS → JSON.
   * @param {number} [settings.palavrasPorMinuto] Velocidade de leitura para estimar o tempo.
   * @param {number} [settings.tempoLimiteMs]     Desiste da busca depois deste tempo.
   */
  constructor({ feed, proxy, palavrasPorMinuto = 200, tempoLimiteMs = 6000 }) {
    this.feedUrl = feed;
    this.converterUrl = proxy;
    this.wordsPerMinute = palavrasPorMinuto;
    this.timeoutMs = tempoLimiteMs;
  }

  /** @returns {Promise<Array<{titulo, data, minutos, resumo, url}>>} */
  async fetchArticles() {
    const abortController = new AbortController();
    const timeoutTimer = setTimeout(() => abortController.abort(), this.timeoutMs);

    try {
      const requestUrl = `${this.converterUrl}${encodeURIComponent(this.feedUrl)}`;
      const response = await fetch(requestUrl, { signal: abortController.signal });
      if (!response.ok) throw new Error(`Medium: HTTP ${response.status}`);

      const feed = await response.json();
      const isValidFeed = feed.status === 'ok' && Array.isArray(feed.items);
      if (!isValidFeed) throw new Error('Medium: resposta inválida');

      return feed.items.map((feedItem) => this.#toArticle(feedItem));
    } finally {
      clearTimeout(timeoutTimer);
    }
  }

  /** Converte um item do feed no formato de artigo do portfólio. */
  #toArticle(feedItem) {
    const articleDocument = MediumService.#parseHtml(feedItem.content || feedItem.description || '');

    const paragraphs = [...articleDocument.querySelectorAll('p')]
      .map((paragraph) => paragraph.textContent.trim())
      .filter(Boolean);

    // Conta o texto inteiro (parágrafos, listas e blocos de código).
    const wordCount = articleDocument.body.textContent.split(/\s+/).filter(Boolean).length;

    return {
      titulo: feedItem.title,
      data: String(feedItem.pubDate || '').slice(0, 10), // "2025-03-27 00:12:06" → "2025-03-27"
      minutos: Math.max(1, Math.round(wordCount / this.wordsPerMinute)),
      resumo: MediumService.#buildSummary(paragraphs),
      url: MediumService.removeTrackingParams(feedItem.link),
    };
  }

  /**
   * Transforma o HTML do artigo num documento apenas para leitura.
   * O DOMParser não executa scripts nem carrega imagens: só lemos o texto.
   */
  static #parseHtml(html) {
    return new DOMParser().parseFromString(html, 'text/html');
  }

  /** Junta os primeiros parágrafos até ~120 caracteres e corta em ~220, sem partir palavras. */
  static #buildSummary(paragraphs) {
    let summary = '';
    for (const paragraph of paragraphs) {
      summary = summary ? `${summary} ${paragraph}` : paragraph;
      if (summary.length >= SUMMARY_MIN_LENGTH) break;
    }

    if (summary.length <= SUMMARY_MAX_LENGTH) return summary;

    const lastSpaceBeforeLimit = summary.lastIndexOf(' ', SUMMARY_MAX_LENGTH);
    return `${summary.slice(0, lastSpaceBeforeLimit)}…`;
  }

  /** Remove o "?source=rss-…" que o Medium coloca nos links, para poder compará-los. */
  static removeTrackingParams(url = '') {
    return String(url).split('?')[0];
  }

  /**
   * Junta os artigos do Medium com os salvos no data.json:
   *   - o resumo escrito à mão no data.json vence o resumo automático;
   *   - artigos antigos que já saíram do feed continuam na lista;
   *   - o resultado fica do mais recente para o mais antigo.
   */
  static mergeWithSaved(mediumArticles = [], savedArticles = []) {
    const savedByUrl = new Map(
      savedArticles.map((article) => [MediumService.removeTrackingParams(article.url), article])
    );

    const updatedArticles = mediumArticles.map((article) => {
      const savedVersion = savedByUrl.get(article.url);
      savedByUrl.delete(article.url);
      if (!savedVersion) return article;
      return { ...article, resumo: savedVersion.resumo || article.resumo };
    });

    const articlesOnlyInDataJson = [...savedByUrl.values()];

    return [...updatedArticles, ...articlesOnlyInDataJson].sort((first, second) =>
      String(second.data).localeCompare(String(first.data))
    );
  }
}
