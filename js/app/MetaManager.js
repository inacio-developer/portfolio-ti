import { readPath } from '../core/utils.js';

/**
 * MetaManager — preenche o que fica fora das seções:
 *   - o idioma da página (<html lang>);
 *   - o título da aba (<title>) e a descrição para buscadores (meta description),
 *     definidos por página em textos.meta.paginas;
 *   - elementos fixos do HTML que pedem texto do JSON:
 *       data-texto="caminho"  → vira o texto do elemento
 *       data-aria="caminho"   → vira o aria-label do elemento
 */
export class MetaManager {
  /**
   * @param {object} data         Conteúdo do data.json.
   * @param {string} currentPage  Chave da página atual ("inicio", "escritos"…).
   */
  apply(data, currentPage) {
    const { textos: uiTexts, perfil: profile } = data;
    const metaTexts = readPath(uiTexts, 'meta', {});
    const pageMeta = readPath(metaTexts, `paginas.${currentPage}`, {});

    if (metaTexts.idioma) document.documentElement.lang = metaTexts.idioma;
    document.title = pageMeta.titulo || profile.nome || '';
    document.querySelector('meta[name="description"]')?.setAttribute('content', pageMeta.descricao || '');

    // Os caminhos no HTML começam com "textos.", por isso o objeto { textos: … }.
    const textSource = { textos: uiTexts };

    document.querySelectorAll('[data-texto]').forEach((element) => {
      element.textContent = readPath(textSource, element.dataset.texto);
    });

    document.querySelectorAll('[data-aria]').forEach((element) => {
      element.setAttribute('aria-label', readPath(textSource, element.dataset.aria));
    });
  }
}
