import { createElement } from '../core/dom.js';
import { asArray } from '../core/utils.js';
import { Component } from './Component.js';

/**
 * Nav — menu entre as páginas do site (textos.navegacao).
 * O link da página atual recebe aria-current="page" (o CSS marca com ■).
 * A página atual vem de this.services.currentPage, definida pelo PortfolioApp.
 */
export class Nav extends Component {
  render() {
    const menuItems = asArray(this.uiText('navegacao', [])).filter((item) => item.rotulo && item.href);
    const hasSomewhereToGo = menuItems.length >= 2;
    if (!hasSomewhereToGo) return null;

    const listItems = menuItems.map((item) => {
      const isCurrentPage = item.pagina === this.services.currentPage;
      return createElement(
        'li',
        {},
        createElement(
          'a',
          { href: item.href, class: 'site-nav__link', 'aria-current': isCurrentPage ? 'page' : null },
          item.rotulo
        )
      );
    });

    return createElement('ul', { class: 'site-nav__list' }, listItems);
  }
}
