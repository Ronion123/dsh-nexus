# Changelog

## 1.0.0 — first release

- Ships the Nexus desktop pet as a dsh-pet character pack.
- Idle animation is the supplied 12-frame transparent loop GIF, encoded to
  VP9-alpha without re-timing so the artist's cadence is preserved.
- The nine-pose action sheet becomes nine point-playable actions in the
  right-click menu (`起手式` … `展翼式`).
- Five transparent high-resolution pose illustrations become the five form
  clips, the pose stickers, and the plugin avatar.
- Persona and all dialogue use the character's classic lines from `台词.md`.
- Host half installs the pack idempotently (content-hash comparison) and keeps
  a byte-stable marker so later releases can retire clips the user never added.
