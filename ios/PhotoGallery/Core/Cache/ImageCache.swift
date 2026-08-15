import Kingfisher
import Foundation

enum ImageCache {
    static func configure() {
        let cache = KingfisherManager.shared.cache
        cache.diskStorage.config.sizeLimit = 200 * 1024 * 1024
        cache.memoryStorage.config.totalCostLimit = 50 * 1024 * 1024
        KingfisherManager.shared.downloader.downloadTimeout = 30
    }

    /// Returns a Source that downloads from `url` but caches under the URL path
    /// (without query string) so presigned URL rotation doesn't bust the cache.
    static func source(for url: URL) -> Source {
        var components = URLComponents(url: url, resolvingAgainstBaseURL: false)
        components?.query = nil
        let cacheKey = components?.url?.absoluteString ?? url.absoluteString
        let resource = KF.ImageResource(downloadURL: url, cacheKey: cacheKey)
        return .network(resource)
    }
}
