import { createElement } from '../core/dom.js';
import { asArray, fillTemplate, groupByField } from '../core/utils.js';
import { Section } from './Section.js';

/**
 * Projects — seção "Projetos".
 *
 * Se os projetos tiverem o campo `categoria`, eles são agrupados e cada grupo
 * ganha um subtítulo (textos.secoes.projetos.categorias). Com uma categoria só,
 * a lista aparece sem subtítulo.
 */
export class Projects extends Section {
  static id = 'projetos';

  get title() {
    return this.uiText('secoes.projetos.titulo');
  }

  content() {
    const projects = asArray(this.data.projetos).filter((project) => project.titulo);
    if (projects.length === 0) return [];

    const projectsByCategory = groupByField(projects, 'categoria');
    const categoryNames = this.uiText('secoes.projetos.categorias', {});
    const showCategoryTitles = projectsByCategory.size > 1;

    return [...projectsByCategory].map(([category, projectsInCategory]) =>
      createElement(
        'div',
        { class: 'project-group' },
        showCategoryTitles && categoryNames[category]
          ? createElement('h3', { class: 'group-title' }, categoryNames[category])
          : null,
        createElement('ol', { class: 'projects' }, projectsInCategory.map((project) => this.#projectItem(project)))
      )
    );
  }

  #projectItem(project) {
    return createElement(
      'li',
      { class: 'project' },
      this.#titleRow(project),
      this.#involvement(project),
      project.resumo ? createElement('p', { class: 'project__summary' }, project.resumo) : null,
      project.resultado ? createElement('p', { class: 'project__result' }, project.resultado) : null,
      this.#technologiesAndCode(project)
    );
  }

  /** Título à esquerda (com link, se houver) e ano à direita (ou o papel, sem ano). */
  #titleRow(project) {
    const title = project.url ? this.link(project.url, project.titulo) : project.titulo;
    const sideNote = project.ano || project.papel;

    return createElement(
      'div',
      { class: 'project__head' },
      createElement('h3', { class: 'project__title' }, title),
      sideNote ? createElement('span', { class: 'project__year' }, sideNote) : null
    );
  }

  /**
   * Sublegenda de envolvimento, ex.: "Desenvolvido como {cargo} na {empresa}".
   * O modelo da frase fica em textos.secoes.projetos.vinculo.
   */
  #involvement(project) {
    const sentenceTemplate = this.uiText('secoes.projetos.vinculo');
    const involvement = project.vinculo;
    if (!sentenceTemplate || !involvement?.cargo || !involvement?.empresa) return null;

    return createElement('p', { class: 'project__context' }, fillTemplate(sentenceTemplate, involvement));
  }

  /** Tecnologias à esquerda, link "Código" à direita. */
  #technologiesAndCode(project) {
    const technologies = asArray(project.tecnologias);
    const hasTechnologies = technologies.length > 0;
    if (!hasTechnologies && !project.repositorio) return null;

    const codeLabel = this.uiText('secoes.projetos.rotuloCodigo');

    return createElement(
      'p',
      { class: 'project__meta' },
      hasTechnologies ? createElement('span', {}, technologies.join(this.listSeparator)) : null,
      project.repositorio ? this.link(project.repositorio, codeLabel, 'link--quiet') : null
    );
  }
}
