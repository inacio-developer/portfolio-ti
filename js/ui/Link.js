import { createElement } from '../core/dom.js';
import { isExternalUrl } from '../core/utils.js';

/**
 * Cria um link com o efeito "marca-texto" (assinatura #2 — ver style.css §10).
 *
 * Links externos:
 *   - abrem em nova aba;
 *   - ganham a seta ↗ (desenhada pelo CSS);
 *   - recebem um aviso de "abre em nova aba" lido apenas por leitores de tela.
 *
 * @param {object} options
 * @param {string} options.url
 * @param {string} options.label           Texto visível do link.
 * @param {string} [options.newTabWarning] Aviso para leitores de tela em links externos.
 * @param {string} [options.extraClass]    Variação visual, ex.: 'link--quiet'.
 * @returns {HTMLAnchorElement|null}       null quando falta url ou texto.
 */
export function createLink({ url, label, newTabWarning = '', extraClass = '' }) {
  if (!url || !label) return null;

  const isExternal = isExternalUrl(url);
  const classNames = ['link', isExternal ? 'link--external' : '', extraClass].filter(Boolean).join(' ');

  const screenReaderWarning =
    isExternal && newTabWarning ? createElement('span', { class: 'sr-only' }, ` ${newTabWarning}`) : null;

  return createElement(
    'a',
    {
      href: url,
      class: classNames,
      target: isExternal ? '_blank' : null,
      rel: isExternal ? 'noopener noreferrer' : null,
    },
    label,
    screenReaderWarning
  );
}
