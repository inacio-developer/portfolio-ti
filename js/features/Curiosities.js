import { createElement } from '../core/dom.js';
import { asArray } from '../core/utils.js';

/**
 * Curiosities — desenhos pessoais que surgem, de vez em quando, nas margens da página.
 *
 * A ideia: quem está lendo nota um rabisco no canto, pensa "hmm, o que é isso?",
 * passa o mouse e descobre algo sobre o Rafael ("One Piece é o anime favorito…").
 *
 * Ritmo normal:
 *   - nada aparece logo de cara: o primeiro surge depois de alguns segundos;
 *   - tempos sorteados (sem padrão) dentro das faixas de data.curiosidades.ritmo;
 *   - ordem embaralhada, sem repetir até todos terem aparecido.
 *
 * Sequência (data.curiosidades.sequencia):
 *   - quando a pessoa passa o mouse num desenho, outro surge em ~5 s do outro lado;
 *   - se ela continuar descobrindo, a corrente segue até 5 desenhos;
 *   - depois do quinto vem o desenho de continuação ("…"), convidando a ficar;
 *   - se ela ignorar um desenho, a corrente se desfaz e volta o ritmo normal.
 *
 * Cuidados:
 *   - sempre nas margens laterais, nunca sobre o texto;
 *   - enquanto o mouse está sobre um desenho, ele não some;
 *   - com a aba em segundo plano, nada aparece;
 *   - só em telas largas com mouse: no celular não há margem livre nem "passar o mouse".
 */

/** Largura mínima da margem lateral para caber um desenho sem encostar no texto. */
const MIN_MARGIN_PX = 120;
/** Telas onde o recurso é ativado: largas e com mouse (hover de verdade). */
const SUPPORTED_SCREEN = '(min-width: 1000px) and (hover: hover) and (pointer: fine)';
/** Tamanho do desenho na tela (igual ao CSS .curio). */
const DRAWING_SIZE_PX = 76;
/** Depois que o mouse sai de um desenho vencido, quanto esperar para ele sumir. */
const LINGER_AFTER_HOVER_MS = 1500;
/** Duração da animação de saída (igual ao CSS .curio.is-leaving). */
const EXIT_ANIMATION_MS = 1200;

const DEFAULT_TIMING = {
  primeiraAposSegundos: [15, 40],
  duracaoSegundos: [20, 75],
  intervaloSegundos: [30, 100],
};

const DEFAULT_SEQUENCE = {
  tamanho: 5,
  atrasoSegundos: 5,
  continuacao: null,
};

/* -------------------------------------------------------------------- */
/* Funções de sorteio                                                    */
/* -------------------------------------------------------------------- */

function randomBetween(min, max) {
  return min + Math.random() * (max - min);
}

/** Sorteia um tempo dentro de uma faixa em segundos e devolve em milissegundos. */
function randomMs([minSeconds, maxSeconds]) {
  return randomBetween(minSeconds, maxSeconds) * 1000;
}

/** Embaralha uma cópia da lista (algoritmo de Fisher–Yates). */
function shuffled(items) {
  const copy = [...items];
  for (let index = copy.length - 1; index > 0; index--) {
    const randomIndex = Math.floor(Math.random() * (index + 1));
    [copy[index], copy[randomIndex]] = [copy[randomIndex], copy[index]];
  }
  return copy;
}

function oppositeSide(side) {
  return side === 'left' ? 'right' : 'left';
}

/* -------------------------------------------------------------------- */

export class Curiosities {
  #items;
  #timing;
  #sequence;

  /** Fila embaralhada dos próximos desenhos. */
  #upcomingItems = [];
  /** Desenhos na tela agora. Na prática, no máximo um: o próximo só surge depois que ele sai. */
  #visibleDoodles = new Set();
  /** Próximo desenho que já deveria ter surgido, mas está esperando a pessoa tirar o mouse do atual. */
  #waitingToAppear = null;
  /** true enquanto um desenho sai e o próximo entra (evita agendar um terceiro no meio da troca). */
  #isSwappingDoodles = false;
  /** Timer do próximo desenho a aparecer (ritmo normal ou sequência). */
  #nextAppearanceTimer = null;
  /** Quantos desenhos seguidos a pessoa já descobriu passando o mouse. */
  #discoveryStreak = 0;
  #lastSide = null;

  /**
   * @param {object} settings  data.curiosidades
   * @param {Array<{icone: string, legenda: string}>} settings.itens
   * @param {object} [settings.ritmo]      Faixas de tempo em segundos: [mínimo, máximo].
   * @param {object} [settings.sequencia]  { tamanho, atrasoSegundos, continuacao: { icone, legenda } }
   */
  constructor({ itens, ritmo, sequencia } = {}) {
    this.#items = asArray(itens).filter((item) => item.icone && item.legenda);
    this.#timing = { ...DEFAULT_TIMING, ...ritmo };
    this.#sequence = { ...DEFAULT_SEQUENCE, ...sequencia };
  }

  start() {
    if (this.#items.length === 0) return;
    if (!window.matchMedia(SUPPORTED_SCREEN).matches) return;

    this.#scheduleRandomAppearance(this.#timing.primeiraAposSegundos);
    window.addEventListener('resize', () => this.#hideAllIfMarginsTooNarrow());
  }

  /* ------------------------------------------------------------------ */
  /* Agenda                                                              */
  /* ------------------------------------------------------------------ */

  /** Ritmo normal: um desenho qualquer da fila, num lado qualquer, depois de um tempo sorteado. */
  #scheduleRandomAppearance(delayRange) {
    this.#scheduleAppearance(randomMs(delayRange), () => ({
      item: this.#takeNextItem(),
      side: this.#chooseSide(),
      isContinuation: false,
    }));
  }

  /** Sequência: o próximo desenho vem rápido e do lado oposto ao que a pessoa acabou de ver. */
  #scheduleSequenceAppearance(previousSide, isContinuation) {
    const delayMs = this.#sequence.atrasoSegundos * 1000;
    this.#scheduleAppearance(delayMs, () => ({
      item: isContinuation ? this.#sequence.continuacao : this.#takeNextItem(),
      side: oppositeSide(previousSide),
      isContinuation,
    }));
  }

  /** Só existe um "próximo desenho" agendado por vez; agendar de novo substitui o anterior. */
  #scheduleAppearance(delayMs, chooseWhatToShow) {
    clearTimeout(this.#nextAppearanceTimer);
    this.#nextAppearanceTimer = setTimeout(() => {
      this.#nextAppearanceTimer = null;
      this.#show(chooseWhatToShow());
    }, delayMs);
  }

  /** Próximo item da fila embaralhada; quando a fila acaba, embaralha de novo. */
  #takeNextItem() {
    if (this.#upcomingItems.length === 0) this.#upcomingItems = shuffled(this.#items);
    return this.#upcomingItems.shift();
  }

  /**
   * Na maioria das vezes (70%) troca de lado em relação ao último desenho,
   * para não parecer que "mora" num canto; nas outras, sorteia.
   * @returns {'left'|'right'}
   */
  #chooseSide() {
    const randomSide = Math.random() < 0.5 ? 'left' : 'right';
    if (!this.#lastSide) return randomSide;

    const shouldSwitchSide = Math.random() < 0.7;
    return shouldSwitchSide ? oppositeSide(this.#lastSide) : randomSide;
  }

  /* ------------------------------------------------------------------ */
  /* Aparecer                                                            */
  /* ------------------------------------------------------------------ */

  async #show(request) {
    // Alguém está olhando um desenho: o próximo espera a pessoa tirar o mouse.
    if (this.#isAnyDoodleHovered()) {
      this.#waitingToAppear = request;
      return;
    }

    const { item, side, isContinuation } = request;
    const sideMargin = this.#sideMarginWidth();

    // Aba escondida ou janela estreita demais: tenta de novo daqui a pouco.
    if (!item || document.hidden || sideMargin < MIN_MARGIN_PX) {
      this.#scheduleRandomAppearance([10, 20]);
      return;
    }

    this.#isSwappingDoodles = true;
    try {
      await this.#appear({ item, side, isContinuation, sideMargin });
    } finally {
      this.#isSwappingDoodles = false;
    }
  }

  /** Um de cada vez: tira o desenho atual, espera ele se apagar e só então desenha o próximo. */
  async #appear({ item, side, isContinuation, sideMargin }) {
    if (this.#visibleDoodles.size > 0) {
      for (const doodle of this.#visibleDoodles) this.#hide(doodle);
      await new Promise((resolve) => setTimeout(resolve, EXIT_ANIMATION_MS));
    }

    const doodle = {
      item,
      side,
      isContinuation,
      element: null,
      isHovered: false,
      wasDiscovered: false,
      timeIsUp: false,
      timer: null,
    };
    doodle.element = this.#createElement(doodle);

    // Só mostra depois que a imagem carregou, para o "traço" não começar vazio.
    try {
      await doodle.element.querySelector('img').decode();
    } catch {
      this.#scheduleRandomAppearance(this.#timing.intervaloSegundos);
      return;
    }

    this.#placeInMargin(doodle, sideMargin);

    document.body.append(doodle.element);
    this.#visibleDoodles.add(doodle);
    this.#lastSide = side;

    doodle.timer = setTimeout(() => this.#onTimeUp(doodle), randomMs(this.#timing.duracaoSegundos));
  }

  #createElement(doodle) {
    const { icone: drawingUrl, legenda: caption } = doodle.item;

    const element = createElement(
      'div',
      {
        class: doodle.isContinuation ? 'curio curio--continuation' : 'curio',
        role: 'img',
        'aria-label': caption,
        onMouseEnter: () => this.#onMouseEnter(doodle),
        onMouseLeave: () => this.#onMouseLeave(doodle),
      },
      createElement('img', {
        class: 'curio__drawing',
        src: drawingUrl,
        alt: '',
        width: DRAWING_SIZE_PX,
        height: DRAWING_SIZE_PX,
      }),
      createElement('span', { class: 'curio__caption', 'aria-hidden': 'true' }, caption)
    );

    // Leve inclinação aleatória: parece colado à mão, não alinhado por máquina.
    element.style.setProperty('--tilt', `${randomBetween(-8, 8).toFixed(1)}deg`);
    return element;
  }

  /** Posiciona o desenho numa altura aleatória, no meio da margem do lado escolhido. */
  #placeInMargin(doodle, sideMargin) {
    const wobble = randomBetween(-sideMargin * 0.12, sideMargin * 0.12);
    const distanceFromEdge = sideMargin / 2 - DRAWING_SIZE_PX / 2 + wobble;
    const verticalPosition = randomBetween(18, 72); // em % da altura da janela

    const { style } = doodle.element;
    style.setProperty(doodle.side, `${Math.max(16, distanceFromEdge)}px`);
    style.top = `${verticalPosition}vh`;
    style.setProperty('--caption-width', `${Math.min(220, sideMargin - 32)}px`);
  }

  /** Largura do espaço livre entre a coluna de texto e a borda da janela. */
  #sideMarginWidth() {
    const textColumn = document.querySelector('.page');
    if (!textColumn) return 0;
    return (window.innerWidth - textColumn.getBoundingClientRect().width) / 2;
  }

  /* ------------------------------------------------------------------ */
  /* Interação                                                           */
  /* ------------------------------------------------------------------ */

  #onMouseEnter(doodle) {
    doodle.isHovered = true;

    // Só a primeira passada de mouse em cada desenho conta como "descoberta".
    if (doodle.wasDiscovered) return;
    doodle.wasDiscovered = true;
    this.#onDiscovered(doodle);
  }

  #onMouseLeave(doodle) {
    doodle.isHovered = false;

    // Havia um desenho esperando a vez: agora ele pode surgir (e este sai).
    if (this.#waitingToAppear) {
      const nextRequest = this.#waitingToAppear;
      this.#waitingToAppear = null;
      this.#show(nextRequest);
      return;
    }

    if (!doodle.timeIsUp) return;

    clearTimeout(doodle.timer);
    doodle.timer = setTimeout(() => this.#hide(doodle), LINGER_AFTER_HOVER_MS);
  }

  /**
   * A pessoa descobriu um desenho. Se ainda não completou a sequência,
   * outro aparece logo do outro lado; ao completar, vem o desenho de continuação.
   */
  #onDiscovered(doodle) {
    // A continuação encerra a sequência; dali em diante volta o ritmo normal.
    if (doodle.isContinuation) {
      this.#discoveryStreak = 0;
      return;
    }

    this.#discoveryStreak += 1;

    const sequenceIsComplete = this.#discoveryStreak >= this.#sequence.tamanho;
    const hasContinuationDrawing = Boolean(this.#sequence.continuacao?.icone);

    if (sequenceIsComplete) {
      this.#discoveryStreak = 0;
      if (hasContinuationDrawing) this.#scheduleSequenceAppearance(doodle.side, true);
      return;
    }

    this.#scheduleSequenceAppearance(doodle.side, false);
  }

  /* ------------------------------------------------------------------ */
  /* Sumir                                                               */
  /* ------------------------------------------------------------------ */

  /** O tempo do desenho acabou; se o mouse estiver em cima, espera a pessoa sair. */
  #onTimeUp(doodle) {
    doodle.timeIsUp = true;

    // Ninguém passou o mouse: a sequência (se havia) se desfaz.
    if (!doodle.wasDiscovered) this.#discoveryStreak = 0;

    if (!doodle.isHovered) this.#hide(doodle);
  }

  #isAnyDoodleHovered() {
    return [...this.#visibleDoodles].some((doodle) => doodle.isHovered);
  }

  #hide(doodle) {
    if (!this.#visibleDoodles.has(doodle)) return;

    clearTimeout(doodle.timer);
    this.#visibleDoodles.delete(doodle);

    doodle.element.classList.add('is-leaving');
    setTimeout(() => doodle.element.remove(), EXIT_ANIMATION_MS);

    // Tela vazia e nada a caminho (nem agendado, nem esperando, nem trocando):
    // volta o ritmo normal.
    const nothingOnScreen = this.#visibleDoodles.size === 0;
    const nothingOnTheWay =
      this.#nextAppearanceTimer === null && this.#waitingToAppear === null && !this.#isSwappingDoodles;
    if (nothingOnScreen && nothingOnTheWay) {
      this.#scheduleRandomAppearance(this.#timing.intervaloSegundos);
    }
  }

  #hideAllIfMarginsTooNarrow() {
    if (this.#sideMarginWidth() >= MIN_MARGIN_PX) return;
    for (const doodle of this.#visibleDoodles) this.#hide(doodle);
  }
}
