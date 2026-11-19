import { readPath } from '../core/utils.js';
import { createLink } from '../ui/Link.js';

/**
 * Component — classe base de todos os blocos da página.
 *
 * Todo componente recebe:
 *   - data:     o conteúdo do data.json, já organizado pelo PortfolioService;
 *   - services: ferramentas compartilhadas, entregues pelo PortfolioApp
 *               (ex.: announcer, para falar com leitores de tela).
 *
 * Cada subclasse implementa render(), que devolve um elemento,
 * uma lista de elementos ou null (quando não há nada para mostrar).
 */
export class Component {
  /**
   * @param {object} data
   * @param {object} [services]
   */
  constructor(data, services = {}) {
    this.data = data;
    this.services = services;
  }

  /** Atalho para data.perfil. */
  get profile() {
    return this.data.perfil;
  }

  /**
   * Busca um texto da interface em data.textos.
   * @example this.uiText('secoes.sobre.titulo') // 'Sobre'
   */
  uiText(path, defaultValue = '') {
    return readPath(this.data.textos, path, defaultValue);
  }

  /** Cria um link no padrão do site, já com o aviso de nova aba vindo do JSON. */
  link(url, label, extraClass = '') {
    return createLink({
      url,
      label,
      extraClass,
      newTabWarning: this.uiText('acessibilidade.novaAba'),
    });
  }

  /** @returns {Node|Node[]|null} */
  render() {
    throw new Error(`${this.constructor.name} precisa implementar render().`);
  }
}
