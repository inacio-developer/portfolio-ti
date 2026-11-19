import { createElement } from '../core/dom.js';
import { asArray } from '../core/utils.js';
import { Section } from './Section.js';

/**
 * Skills — seção "Competências": nome do grupo à esquerda,
 * itens separados por " · " à direita (perfil.ferramentas).
 */
export class Skills extends Section {
  static id = 'ferramentas';

  get title() {
    return this.uiText('secoes.ferramentas.titulo');
  }

  content() {
    const skillGroups = asArray(this.profile.ferramentas).filter(
      (group) => group.grupo && asArray(group.itens).length > 0
    );
    if (skillGroups.length === 0) return [];

    const rows = skillGroups.map((group) => [
      createElement('dt', {}, group.grupo),
      createElement('dd', {}, asArray(group.itens).join(this.listSeparator)),
    ]);

    return createElement('dl', { class: 'tools' }, rows);
  }
}
