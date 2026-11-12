# Brand asset provenance

These existing product assets were copied unchanged from the local IYBA product checkouts. They are used to identify the products in this help center; no new logo artwork was generated. Source paths below are relative to the parent IYBA workspace.

## branding/iyba-logo-white.png

- Source: `iybaorg/public/assets/img/iyba-logo-white.png`
- Destination: `docs/assets/branding/iyba-logo-white.png`
- Usage: IYBA white wordmark; the same white wordmark is used in `iybaorg/resources/views/partials/home_footer.blade.php:62` via `public/home/images/iyba-logo-white.png`.
- SHA-256: `5700c026f36e505d43840e5535c86e92fddd2a418098ac7264b3daef84261948`

## iyba/iyba-logo.png

- Source: `iybaorg/public/assets/img/iyba-logo.png`
- Destination: `docs/assets/iyba/iyba-logo.png`
- Usage: IYBA navy wordmark, referenced by `iybaorg/resources/views/partials/home_header.blade.php:58`.
- SHA-256: `bfde2450270f4aebb207950f217a5b67839e958a0cb3d3d2383f9481aed4c045`

## yachtbroker/yachtbroker-logo.png

- Source: `iyba-portal/public/logo/yachtbroker_blue.png`
- Destination: `docs/assets/yachtbroker/yachtbroker-logo.png`
- Usage: YachtBroker orange/navy wordmark, referenced by `iyba-portal/resources/views/emails/notifications/searched-vessel-notification.blade.php:13`.
- SHA-256: `f035a872324077407771ca86b2ad18d0be68d980a9a729267e37293d02bcddb0`

## boatdox/boatdox-logo.png

- Source: `boatdox_uat_prod/front/public/images/boatdox-logo-blue.png`
- Destination: `docs/assets/boatdox/boatdox-logo.png`
- Usage: BoatDox navy/cyan logo, referenced by `boatdox_uat_prod/front/src/components/auth/forms/Verify.jsx:90`.
- SHA-256: `7bf723687b7cca5faa4a4cc840377dd8ec5687048fb73c25fd550e4c8e941ec5`

## Presentation

Product landing pages use the `product-logo` CSS class. Keep a light background behind the navy wordmarks in both color modes. The white IYBA wordmark is intended for the global dark header. Preserve each asset’s aspect ratio and descriptive alternative text.
