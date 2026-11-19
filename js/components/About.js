import { createElement } from '../core/dom.js';
import { asArray } from '../core/utils.js';
import { Section } from './Section.js';

/**
 * About — seção "Sobre": a bio em texto corrido, um parágrafo por item de perfil.bio.
 */
export class About extends Section {
  static id = 'sobre';

  get title() {
    return this.uiText('secoes.sobre.titulo');
  }

  content() {
    const paragraphs = asArray(this.profile.bio);
    if (paragraphs.length === 0) return [];

    const paragraphElements = paragraphs.map((paragraphText) => createElement('p', {}, paragraphText));
    return createElement('div', { class: 'prose' }, paragraphElements);
  }
}
