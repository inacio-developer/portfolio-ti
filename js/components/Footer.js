import { createElement } from '../core/dom.js';
import { fillTemplate } from '../core/utils.js';
import { Component } from './Component.js';

/**
 * Footer — rodapé "© {ano} {nome}".
 * O ■ de fim de matéria é desenhado pelo CSS (.footer__text::after).
 */
export class Footer extends Component {
  render() {
    const footerTemplate = this.uiText('rodape.texto');
    if (!footerTemplate) return null;

    const footerText = fillTemplate(footerTemplate, {
      ano: new Date().getFullYear(),
      nome: this.profile.nome || '',
    });

    return createElement('p', { class: 'footer__text' }, footerText);
  }
}
