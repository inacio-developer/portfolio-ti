import { createElement } from '../core/dom.js';

/**
 * EdgeScrollNavigation — troca de página ao "rolar além da borda".
 *
 *   Página inicial: chegou ao fim e continuou rolando para baixo → vai para Escritos.
 *   Página Escritos: chegou ao topo e continuou rolando para cima → volta ao início
 *                    (e chega lá no fim da página, como quem subiu de volta).
 *
 * Para não levar ninguém para outra página sem querer:
 *   - só conta a rolagem feita DEPOIS de já estar parado na borda (a inércia de
 *     quem acabou de chegar ao fim não vale);
 *   - um aviso discreto aparece ("Continue rolando para…") com uma barrinha que
 *     enche conforme a pessoa insiste; só quando enche a página muda;
 *   - se a pessoa para de rolar, a barra esvazia e o aviso some.
 *
 * Funciona com roda do mouse / touchpad (wheel) e com o dedo (touch).
 */

/** Quanto é preciso "insistir" além da borda, em pixels de rolagem. */
const SCROLL_NEEDED_PX = 650;
/** Tempo parado na borda antes de começar a contar (ignora a inércia da chegada). */
const SETTLE_AT_EDGE_MS = 350;
/** Sem rolar por este tempo, o progresso zera e o aviso some. */
const GIVE_UP_AFTER_MS = 700;
/** No toque, cada pixel arrastado vale mais (o dedo percorre distâncias menores). */
const TOUCH_MULTIPLIER = 2.5;
/** Tolerância para considerar que chegou ao fim/topo. */
const EDGE_TOLERANCE_PX = 2;
/** Duração do esmaecimento da página antes de trocar (igual ao CSS .is-leaving-page). */
const PAGE_EXIT_MS = 250;

/** Chave usada para avisar a próxima página de onde a pessoa veio. */
const ARRIVAL_KEY = 'portfolio:chegada';

export class EdgeScrollNavigation {
  #direction;
  #targetUrl;
  #message;
  #arriveAtBottom;

  #progressPx = 0;
  #reachedEdgeAt = null;
  #giveUpTimer = null;
  #touchStartY = null;
  #isLeaving = false;
  #hint = null;
  #hintFill = null;

  /**
   * @param {object} options
   * @param {'down'|'up'} options.direction  Para onde é preciso rolar além da borda.
   * @param {string} options.targetUrl       Página de destino.
   * @param {string} options.message         Texto do aviso (vem do data.json).
   * @param {boolean} [options.arriveAtBottom] Se o destino deve abrir já no fim da página.
   */
  constructor({ direction, targetUrl, message, arriveAtBottom = false }) {
    this.#direction = direction;
    this.#targetUrl = targetUrl;
    this.#message = message;
    this.#arriveAtBottom = arriveAtBottom;
  }

  start() {
    if (!this.#targetUrl) return;

    this.#hint = this.#createHint();
    document.body.append(this.#hint);

    window.addEventListener('scroll', () => this.#onScroll(), { passive: true });
    window.addEventListener('wheel', (event) => this.#onWheel(event), { passive: true });
    window.addEventListener('touchstart', (event) => this.#onTouchStart(event), { passive: true });
    window.addEventListener('touchmove', (event) => this.#onTouchMove(event), { passive: true });
    window.addEventListener('touchend', () => this.#onTouchEnd(), { passive: true });

    // Botão "voltar" do navegador pode restaurar esta página exatamente como
    // estava ao sair (já esmaecida). Nesse caso, desfaz a saída.
    window.addEventListener('pageshow', (event) => {
      if (event.persisted) this.#cancelLeaving();
    });

    this.#onScroll();
  }

  #cancelLeaving() {
    this.#isLeaving = false;
    document.body.classList.remove('is-leaving-page');
    this.#reset();
  }

  /**
   * Se a pessoa chegou vindo de baixo (da página de Escritos para o início),
   * abre a página já no fim. Chamado pelo PortfolioApp depois de montar a página.
   */
  static restoreArrivalPosition() {
    let arrival = null;
    try {
      arrival = sessionStorage.getItem(ARRIVAL_KEY);
      sessionStorage.removeItem(ARRIVAL_KEY);
    } catch {
      return; // armazenamento bloqueado: abre no topo, sem problema
    }

    if (arrival === 'fim') {
      window.scrollTo({ top: document.documentElement.scrollHeight, behavior: 'instant' });
    }
  }

  /* ------------------------------------------------------------------ */
  /* Onde a pessoa está                                                  */
  /* ------------------------------------------------------------------ */

  #isAtEdge() {
    const { scrollY, innerHeight } = window;
    const pageHeight = document.documentElement.scrollHeight;

    if (this.#direction === 'down') return scrollY + innerHeight >= pageHeight - EDGE_TOLERANCE_PX;
    return scrollY <= EDGE_TOLERANCE_PX;
  }

  /** Marca o momento em que a borda foi alcançada (ou esquece, se saiu dela). */
  #onScroll() {
    if (this.#isAtEdge()) {
      this.#reachedEdgeAt ??= performance.now();
    } else {
      this.#reachedEdgeAt = null;
      this.#reset();
    }
  }

  /** Já está na borda há tempo suficiente para a inércia da chegada ter acabado? */
  #hasSettledAtEdge() {
    if (!this.#isAtEdge() || this.#reachedEdgeAt === null) return false;
    return performance.now() - this.#reachedEdgeAt >= SETTLE_AT_EDGE_MS;
  }

  /* ------------------------------------------------------------------ */
  /* Roda do mouse / touchpad                                            */
  /* ------------------------------------------------------------------ */

  #onWheel(event) {
    this.#onScroll();

    const scrollingDown = event.deltaY > 0;
    const isTowardTheEdge = this.#direction === 'down' ? scrollingDown : !scrollingDown;

    if (!isTowardTheEdge) {
      this.#reset();
      return;
    }
    if (!this.#hasSettledAtEdge()) return;

    // deltaMode 1 = rolagem em linhas (alguns mouses); converte para pixels.
    const pixels = Math.abs(event.deltaY) * (event.deltaMode === 1 ? 16 : 1);
    this.#addProgress(pixels);
  }

  /* ------------------------------------------------------------------ */
  /* Toque (celular)                                                     */
  /* ------------------------------------------------------------------ */

  #onTouchStart(event) {
    this.#touchStartY = this.#hasSettledAtEdge() ? event.touches[0].clientY : null;
  }

  #onTouchMove(event) {
    if (this.#touchStartY === null) return;

    // Dedo subindo = página rolando para baixo.
    const fingerTravel = this.#touchStartY - event.touches[0].clientY;
    const pullTowardEdge = this.#direction === 'down' ? fingerTravel : -fingerTravel;

    this.#setProgress(Math.max(0, pullTowardEdge) * TOUCH_MULTIPLIER);
  }

  #onTouchEnd() {
    this.#touchStartY = null;
    if (this.#progressPx < SCROLL_NEEDED_PX) this.#reset();
  }

  /* ------------------------------------------------------------------ */
  /* Progresso e aviso                                                   */
  /* ------------------------------------------------------------------ */

  #addProgress(pixels) {
    this.#setProgress(this.#progressPx + pixels);

    // Parou de insistir? Desiste depois de um instante.
    clearTimeout(this.#giveUpTimer);
    this.#giveUpTimer = setTimeout(() => this.#reset(), GIVE_UP_AFTER_MS);
  }

  #setProgress(pixels) {
    if (this.#isLeaving) return;

    this.#progressPx = Math.min(pixels, SCROLL_NEEDED_PX);
    const fraction = this.#progressPx / SCROLL_NEEDED_PX;

    this.#hint.classList.toggle('is-visible', fraction > 0);
    this.#hintFill.style.transform = `scaleX(${fraction})`;

    if (fraction >= 1) this.#goToTarget();
  }

  /** Zera o progresso e esconde o aviso (a não ser que a página já esteja trocando). */
  #reset() {
    if (this.#isLeaving) return;
    clearTimeout(this.#giveUpTimer);
    this.#progressPx = 0;
    this.#hint.classList.remove('is-visible');
    this.#hintFill.style.transform = 'scaleX(0)';
  }

  #createHint() {
    this.#hintFill = createElement('span', { class: 'edge-hint__fill' });

    return createElement(
      'div',
      { class: `edge-hint edge-hint--${this.#direction}`, 'aria-hidden': 'true' },
      createElement('span', { class: 'edge-hint__label' }, this.#message),
      createElement('span', { class: 'edge-hint__bar' }, this.#hintFill)
    );
  }

  /* ------------------------------------------------------------------ */
  /* Trocar de página                                                    */
  /* ------------------------------------------------------------------ */

  #goToTarget() {
    this.#isLeaving = true;

    if (this.#arriveAtBottom) {
      try {
        sessionStorage.setItem(ARRIVAL_KEY, 'fim');
      } catch {
        // sem armazenamento: o destino abre no topo, tudo bem
      }
    }

    document.body.classList.add('is-leaving-page');
    setTimeout(() => window.location.assign(this.#targetUrl), PAGE_EXIT_MS);
  }
}
