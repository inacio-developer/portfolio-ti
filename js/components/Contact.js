import { createElement } from '../core/dom.js';
import { asArray } from '../core/utils.js';
import { ClipboardService } from '../services/ClipboardService.js';
import { Section } from './Section.js';

/** Quanto tempo o botão fica mostrando "Copiado" antes de voltar ao normal. */
const COPIED_FEEDBACK_DURATION_MS = 2000;

/**
 * Contact — seção "Contato": e-mail com botão de copiar e contatos extras.
 * Usa o announcer (this.services.announcer) para avisar leitores de tela.
 */
export class Contact extends Section {
  static id = 'contato';

  #resetButtonTimer = null;

  get #sectionTexts() {
    return this.uiText('secoes.contato', {});
  }

  get title() {
    return this.#sectionTexts.titulo;
  }

  content() {
    const otherContacts = asArray(this.profile.contatos);
    if (!this.profile.email && otherContacts.length === 0) return [];

    const introduction = this.#sectionTexts.texto;

    return [
      introduction ? createElement('p', { class: 'contact__text' }, introduction) : null,
      this.#emailWithCopyButton(),
      this.#otherContacts(otherContacts),
    ];
  }

  #emailWithCopyButton() {
    const email = this.profile.email;
    if (!email) return null;

    const copyLabel = this.#sectionTexts.copiar;
    const copyButton = copyLabel
      ? createElement('button', {
          type: 'button',
          class: 'copy',
          onClick: (event) => this.#copyEmail(email, event.currentTarget),
        }, copyLabel)
      : null;

    return createElement('p', { class: 'contact__email' }, this.link(`mailto:${email}`, email, 'link--large'), copyButton);
  }

  #otherContacts(contacts) {
    if (contacts.length === 0) return null;
    const listItems = contacts.map((contact) => createElement('li', {}, this.link(contact.url, contact.rotulo)));
    return createElement('ul', { class: 'inline-list' }, listItems);
  }

  async #copyEmail(email, button) {
    const wasCopied = await ClipboardService.copy(email);

    // Sem acesso à área de transferência: abre o programa de e-mail como alternativa.
    if (!wasCopied) {
      location.href = `mailto:${email}`;
      return;
    }

    const { copiar: copyLabel, copiado: copiedLabel } = this.#sectionTexts;
    const { announcer } = this.services;

    button.textContent = copiedLabel;
    button.classList.add('is-done');
    announcer?.say(copiedLabel);

    clearTimeout(this.#resetButtonTimer);
    this.#resetButtonTimer = setTimeout(() => {
      button.textContent = copyLabel;
      button.classList.remove('is-done');
      announcer?.clear();
    }, COPIED_FEEDBACK_DURATION_MS);
  }
}
