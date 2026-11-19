import { createElement } from '../core/dom.js';
import { asArray } from '../core/utils.js';
import { Component } from './Component.js';

/**
 * Hero — topo da página inicial: foto (opcional), nome, cargo, frase de abertura e links.
 * É montado dentro de <header id="hero">.
 */
export class Hero extends Component {
  render() {
    return [this.#photo(), this.#name(), this.#roleAndLocation(), this.#openingLine(), this.#profileLinks()];
  }

  #photo() {
    const photoUrl = this.profile.avatar;
    if (!photoUrl) return null;

    return createElement('img', {
      class: 'hero__avatar',
      src: photoUrl,
      alt: this.uiText('acessibilidade.fotoPerfil'),
      width: 64,
      height: 64,
      decoding: 'async',
    });
  }

  /** Assinatura #1: o cursor de redação (span.caret) aparece logo depois do nome. */
  #name() {
    const blinkingCursor = createElement('span', { class: 'caret', 'aria-hidden': 'true' });
    return createElement('h1', { class: 'hero__name' }, this.profile.nome, blinkingCursor);
  }

  #roleAndLocation() {
    const { cargo: role, localizacao: location } = this.profile;
    if (!role && !location) return null;

    const locationElement = location ? createElement('span', { class: 'hero__place' }, location) : null;
    return createElement('p', { class: 'hero__role' }, role, locationElement);
  }

  #openingLine() {
    const openingLine = this.profile.lede;
    return openingLine ? createElement('p', { class: 'hero__lede' }, openingLine) : null;
  }

  #profileLinks() {
    const links = asArray(this.profile.links);
    if (links.length === 0) return null;

    const listItems = links.map((link) => createElement('li', {}, this.link(link.url, link.rotulo)));

    return createElement(
      'nav',
      { class: 'hero__links', 'aria-label': this.uiText('acessibilidade.navegacaoLinks') },
      createElement('ul', { class: 'inline-list' }, listItems)
    );
  }
}
