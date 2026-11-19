/**
 * Criação de elementos HTML.
 *
 * Toda a interface é montada com createElement(): cada texto vindo do JSON
 * entra como texto puro (textContent), nunca como HTML. Assim, um "<script>"
 * escrito num artigo do Medium aparece como texto e não é executado.
 *
 * @example
 *   createElement('a', { href: '/contato', class: 'link' }, 'Fale comigo')
 *   // → <a href="/contato" class="link">Fale comigo</a>
 *
 * @example  Elementos dentro de elementos:
 *   createElement('ul', { class: 'lista' },
 *     createElement('li', {}, 'Primeiro'),
 *     createElement('li', {}, 'Segundo'),
 *   )
 */

/** Valores que não viram atributo nem conteúdo (permite escrever `condicao ? x : null`). */
function isNothing(value) {
  return value === null || value === undefined || value === false || value === '';
}

/**
 * Cria um elemento HTML.
 *
 * @param {string} tagName       Nome da tag: 'div', 'p', 'a'…
 * @param {object} [attributes]  Atributos. 'class' vira className; funções 'onClick' viram eventos.
 * @param {...any} children      Conteúdo: textos, elementos ou listas deles (podem ser aninhadas).
 * @returns {HTMLElement}
 */
export function createElement(tagName, attributes = {}, ...children) {
  const element = document.createElement(tagName);

  for (const [name, value] of Object.entries(attributes)) {
    if (isNothing(value)) continue;

    const isEventHandler = name.startsWith('on') && typeof value === 'function';

    if (name === 'class') {
      element.className = value;
    } else if (isEventHandler) {
      const eventName = name.slice(2).toLowerCase(); // onClick → click
      element.addEventListener(eventName, value);
    } else {
      element.setAttribute(name, value === true ? '' : value);
    }
  }

  for (const child of children.flat(Infinity)) {
    if (isNothing(child)) continue;
    element.append(child instanceof Node ? child : String(child));
  }

  return element;
}

/**
 * Um render() pode devolver um elemento, uma lista de elementos ou null.
 * Esta função transforma qualquer um desses casos numa lista simples de elementos.
 */
export function toElementList(renderResult) {
  return [renderResult].flat(Infinity).filter((item) => item instanceof Node);
}
