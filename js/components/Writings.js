import { createElement } from '../core/dom.js';
import { asArray, fillTemplate, formatDate } from '../core/utils.js';
import { Section } from './Section.js';

/**
 * Writings — base das listas de artigos (data.escritos.itens).
 *
 * `static updatesWithMedium = true` avisa o PortfolioApp que esta seção deve
 * ser desenhada de novo quando os artigos do Medium terminarem de carregar.
 *
 * As subclasses definem:
 *   static id
 *   get textsPath()  → onde ficam os textos da seção em data.textos
 *   get maxArticles() → quantos artigos mostrar (Infinity = todos)
 */
export class Writings extends Section {
  static updatesWithMedium = true;

  get textsPath() {
    return 'secoes.escritos';
  }

  get maxArticles() {
    return Infinity;
  }

  /** Textos desta seção (título, introdução, link "ver todos"…). */
  get sectionTexts() {
    return this.uiText(this.textsPath, {});
  }

  get title() {
    return this.sectionTexts.titulo;
  }

  get articles() {
    return asArray(this.data.escritos.itens).filter((article) => article.titulo && article.url);
  }

  content() {
    const articlesToShow = this.articles.slice(0, this.maxArticles);
    if (articlesToShow.length === 0) return [];

    const { introducao: introduction, verTodos: seeAllLink } = this.sectionTexts;

    return [
      introduction ? createElement('p', { class: 'section__intro' }, introduction) : null,
      createElement('ol', { class: 'posts' }, articlesToShow.map((article) => this.#articleItem(article))),
      seeAllLink ? createElement('p', { class: 'section__more' }, this.link(seeAllLink.url, seeAllLink.rotulo)) : null,
    ];
  }

  #articleItem(article) {
    return createElement(
      'li',
      { class: 'post' },
      this.#dateAndReadingTime(article),
      createElement('h3', { class: 'post__title' }, this.link(article.url, article.titulo)),
      article.resumo ? createElement('p', { class: 'post__summary' }, article.resumo) : null
    );
  }

  /** Ex.: "27 de mar. de 2025 · 6 min de leitura" */
  #dateAndReadingTime(article) {
    const language = this.uiText('meta.idioma');
    const readingTimeTemplate = this.uiText('secoes.escritos.leitura');

    const dateElement = article.data
      ? createElement('time', { datetime: article.data }, formatDate(article.data, language))
      : null;

    const readingTimeElement =
      article.minutos && readingTimeTemplate
        ? createElement('span', {}, fillTemplate(readingTimeTemplate, { min: article.minutos }))
        : null;

    return createElement('p', { class: 'post__meta' }, dateElement, readingTimeElement);
  }
}

/** Página escritos.html: todos os artigos + link para o perfil no Medium. */
export class WritingsArchive extends Writings {
  static id = 'arquivo';

  get textsPath() {
    return 'secoes.arquivo';
  }
}
