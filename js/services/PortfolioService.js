/**
 * PortfolioService
 * Única responsabilidade: buscar o data.json e devolvê-lo normalizado,
 * para que os componentes nunca precisem checar se uma coleção existe.
 */
export class PortfolioService {
  /** @param {string} url Caminho do arquivo de dados. */
  constructor(url = 'data.json') {
    this.url = url;
  }

  /**
   * @returns {Promise<{
   *   perfil: object, trajetoria: any[], projetos: any[],
   *   escritos: { fonte: object|null, itens: any[] }, textos: object
   * }>}
   */
  async load() {
    // no-cache: o navegador sempre revalida, então edições no JSON aparecem no F5.
    const response = await fetch(this.url, { cache: 'no-cache' });
    if (!response.ok) throw new Error(`${this.url}: HTTP ${response.status}`);
    return PortfolioService.normalize(await response.json());
  }

  /** Garante a forma esperada de cada coleção. */
  static normalize(raw = {}) {
    const object = (v) => (v && typeof v === 'object' && !Array.isArray(v) ? v : {});
    const array = (v) => (Array.isArray(v) ? v : []);
    const escritos = object(raw.escritos);

    return {
      perfil: object(raw.perfil),
      trajetoria: array(raw.trajetoria),
      projetos: array(raw.projetos),
      escritos: {
        fonte: escritos.fonte?.feed && escritos.fonte?.proxy ? escritos.fonte : null,
        itens: array(escritos.itens),
      },
      curiosidades: {
        ritmo: object(object(raw.curiosidades).ritmo),
        sequencia: object(object(raw.curiosidades).sequencia),
        itens: array(object(raw.curiosidades).itens),
      },
      textos: object(raw.textos),
    };
  }
}
