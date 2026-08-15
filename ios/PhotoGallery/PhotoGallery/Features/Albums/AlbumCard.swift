import Kingfisher
import SwiftUI

struct AlbumCard: View {
    let album: Album

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Color.secondary.opacity(0.15)
                .frame(maxWidth: .infinity, minHeight: 140, maxHeight: 140)
                .overlay(
                    KFImage(source: album.coverThumbURL.map { ImageCache.source(for: $0) })
                        .resizable()
                        .scaledToFill()
                )
                .overlay(alignment: .topTrailing) {
                    if album.isLocked {
                        Image(systemName: "lock.fill")
                            .padding(6)
                            .background(.ultraThinMaterial, in: Circle())
                            .padding(8)
                    }
                }
                .clipShape(RoundedRectangle(cornerRadius: 10))

            Text(album.name)
                .font(.subheadline.weight(.semibold))
                .lineLimit(1)

            if let date = album.formattedDate {
                Text(date)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

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
