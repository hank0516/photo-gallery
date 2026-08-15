import Kingfisher
import SwiftUI

struct AlbumCard: View {
    let album: Album

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            ZStack(alignment: .topTrailing) {
                KFImage(source: album.coverThumbURL.map { ImageCache.source(for: $0) })
                    .placeholder { Color.secondary.opacity(0.2) }
                    .resizable()
                    .scaledToFill()
                    .frame(height: 140)
                    .clipped()
                    .cornerRadius(10)

                if album.isLocked {
                    Image(systemName: "lock.fill")
                        .padding(6)
                        .background(.ultraThinMaterial, in: Circle())
                        .padding(8)
                }
            }

            Text(album.name)
                .font(.subheadline.weight(.semibold))
                .lineLimit(1)

            HStack {
                Text("\(album.photoCount) items")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                Spacer()
                RoleBadge(role: album.myRole)
            }
        }
    }
}

private struct RoleBadge: View {
    let role: String
    var body: some View {
        Text(role)
            .font(.caption2.weight(.medium))
            .padding(.horizontal, 6)
            .padding(.vertical, 2)
            .background(color.opacity(0.15), in: Capsule())
            .foregroundStyle(color)
    }
    private var color: Color {
        switch role {
        case "admin":    return .red
        case "uploader": return .orange
        default:         return .blue
        }
    }
}
