/**
 * Announcer
 * Envia mensagens curtas a leitores de tela por uma região aria-live
 * (ex.: "Copiado" depois de copiar o e-mail).
 */
export class Announcer {
  #el;

  /** @param {string} selector Elemento com aria-live no index.html. */
  constructor(selector = '#anuncio') {
    this.#el = document.querySelector(selector);
  }

  say(message) {
    if (this.#el) this.#el.textContent = message;
  }

  clear() {
    this.say('');
  }
}
