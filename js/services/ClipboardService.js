/**
 * ClipboardService
 * Encapsula a API de área de transferência e sua possível falha
 * (contexto não seguro, permissão negada, navegador antigo).
 */
export class ClipboardService {
  /** @returns {Promise<boolean>} true se o texto foi copiado. */
  static async copy(text) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {
      return false;
    }
  }
}
