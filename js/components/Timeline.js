import { createElement } from '../core/dom.js';
import { asArray, groupByField } from '../core/utils.js';
import { Section } from './Section.js';

/**
 * Timeline — seção "Trajetória", agrupada pelo campo `tipo`
 * (experiência, formação, cursos e certificações).
 *
 * Cada item pode ser simples (título, organização, descrição) ou detalhado,
 * no estilo do LinkedIn: uma empresa com um ou mais cargos, e cada cargo com
 * atividades em tópicos, opcionalmente separadas em grupos:
 *
 *   {
 *     "titulo": "Empresa", "organizacao": "Setor · Remoto", "inicio": "2025", "fim": "",
 *     "cargos": [
 *       {
 *         "titulo": "Cargo", "periodo": "jun 2025 - atual",
 *         "grupos": [ { "titulo": "Tema", "itens": ["Atividade 1", "Atividade 2"] } ]
 *       }
 *     ]
 *   }
 *
 * Um cargo também pode ter "itens" direto, sem grupos.
 *
 * Assinatura #3: o fio vertical com marcadores ■ é desenhado pelo CSS (style.css §7).
 */
export class Timeline extends Section {
  static id = 'trajetoria';

  get title() {
    return this.uiText('secoes.trajetoria.titulo');
  }

  content() {
    const entries = asArray(this.data.trajetoria).filter((entry) => entry.titulo);
    if (entries.length === 0) return [];

    const groupNames = this.uiText('secoes.trajetoria.grupos', {});

    return [...groupByField(entries, 'tipo')].map(([type, entriesOfType]) =>
      createElement(
        'div',
        { class: 'timeline-group' },
        groupNames[type] ? createElement('h3', { class: 'group-title' }, groupNames[type]) : null,
        createElement('ol', { class: 'timeline' }, entriesOfType.map((entry) => this.#timelineItem(entry)))
      )
    );
  }

  #timelineItem(entry) {
    return createElement(
      'li',
      { class: 'timeline__item' },
      createElement('span', { class: 'timeline__period' }, this.formatPeriod(entry)),
      createElement(
        'div',
        { class: 'timeline__body' },
        createElement('p', { class: 'timeline__title' }, entry.titulo),
        entry.organizacao ? createElement('p', { class: 'timeline__org' }, entry.organizacao) : null,
        entry.descricao ? createElement('p', { class: 'timeline__desc' }, entry.descricao) : null,
        this.#roles(entry)
      )
    );
  }

  /* ------------------------------------------------------------------ */
  /* Cargos (estilo LinkedIn)                                            */
  /* ------------------------------------------------------------------ */

  #roles(entry) {
    const roles = asArray(entry.cargos).filter((role) => role.titulo);
    if (roles.length === 0) return null;

    return createElement('ol', { class: 'roles' }, roles.map((role) => this.#role(role)));
  }

  #role(role) {
    return createElement(
      'li',
      { class: 'role' },
      createElement('p', { class: 'role__title' }, role.titulo),
      role.periodo ? createElement('p', { class: 'role__period' }, role.periodo) : null,
      role.resumo ? createElement('p', { class: 'role__summary' }, role.resumo) : null,
      this.#activityList(role.itens),
      asArray(role.grupos).map((group) => this.#activityGroup(group))
    );
  }

  /** Um tema de atividades, ex.: "Arquitetura e performance" + lista de tópicos. */
  #activityGroup(group) {
    const activities = this.#activityList(group.itens);
    if (!activities) return null;

    return createElement(
      'div',
      { class: 'role__group' },
      group.titulo ? createElement('p', { class: 'role__group-title' }, group.titulo) : null,
      activities
    );
  }

  #activityList(items) {
    const activities = asArray(items);
    if (activities.length === 0) return null;
    return createElement('ul', { class: 'role__list' }, activities.map((text) => createElement('li', {}, text)));
  }

  /* ------------------------------------------------------------------ */

  /**
   * Monta o período exibido à esquerda:
   *   início e fim diferentes → "2019 - 2021"
   *   início e fim iguais     → "2021"
   *   sem fim                 → "2025 - Atual"
   */
  formatPeriod({ inicio: start, fim: end }) {
    const endLabel = end || this.uiText('rotulos.atual');
    if (!start) return endLabel;
    if (start === endLabel) return start;

    const separator = this.uiText('rotulos.separadorPeriodo', '-');
    return `${start} ${separator} ${endLabel}`;
  }
}
