# Prose Rights And Access Review

## Scope

This review covers the bounded pilot candidate `பாரதியார் கட்டுரைகள்` at TamilVU.
It is an engineering access review, not legal advice.

## Ownership Observations

- TamilVU displays a site copyright notice for Tamil Virtual Academy.
- The selected work page identifies a Poompuhar publication, so edition, arrangement,
  annotations, and presentation may involve third-party rights.
- Subramania Bharati died in 1921. His underlying writings are an old-work,
  public-domain candidate, but that does not automatically make a modern edition or
  TamilVU's HTML presentation free to reproduce.

## Official Policy Evidence

TamilVU's official website-policy page states that site data may be reproduced after
emailing TamilVU and receiving proper permission. It also says this permission does not
extend to material identified as third-party copyright; authorization must then come from
the relevant department or copyright holder.

Policy URL:
`https://www.tamilvu.org/ta/இணையத்தள-கொள்கைகள்`

## Pilot Decision

Three allowlisted pages were fetched only to inspect hierarchy and calculate source
hashes. Full HTML and TamilVU essay text are not committed. The local fixtures are compact
structural reconstructions, and the prose paragraph text is synthetic Tamil written for
parser testing.

This makes local parser development acceptable without treating the pilot as permission
to reproduce or ingest TamilVU prose. Any source-text fixture or corpus expansion remains
blocked until written permission and edition-level rights are documented.

## Risks Before Scale

- Rights may differ by work, edition, publisher, annotation, image, and page.
- A public-domain author does not settle rights in a later edited publication.
- The inspected essay page is an iframe wrapper that points to another legacy endpoint.
- Large-scale downloading or redistribution is outside this approval.
- Source attribution, URLs, inspection hashes, and rights status must remain attached.

## Required Gate

Before prose corpus ingestion, obtain and record TamilVU permission, identify third-party
edition rights, confirm the exact endpoints permitted, and define redistribution limits.
