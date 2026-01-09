# PySTAC v2.0

**PySTAC v2.0** is a ground-up re-write of **PySTAC**.
Our high-level design goals are a form of [Postel's law](https://en.wikipedia.org/wiki/Robustness_principle):

- Help people make the best STAC possible
- Help people interact with existing (even poorly constructed or invalid) STAC as easily as possible

To do so, we have some specific implementation strategies.

- **Keep the core data structure APIs basically the same**: People are used to the basic methods on `Item`, `Catalog`, `Collection`, etc.
  We shouldn't change the external APIs unless there's a good reason to.
- **Relax core data structure initializers to accept almost anything**, with warnings if something's being changed to make it valid
- **Stay low-dependency by default**: This keeps our maintenance burden lower, at the cost of having to hand-roll more stuff ourselves.
- **Replace "implementation" APIs**: `Item`, `Catalog`, etc are the "what" of **pystac**.
  Things like `StacIO` are the "how".
  We should create replacement structures for any of these "how" interfaces that we want to dramatically change, rather than try to "fix" the existing ones.
  Backwards compatibility will be _much_ more difficult for these "how" interfaces, so we shouldn't even try.
  _If possible_ we should re-write the existing "how" structure (e.g. `StacIO`) to use the new API, but this should be a lower-priority objective.
- **Do fewer things at once**: One of the biggest design problems of PySTAC v1.0 (in this author's opinion) was that many functions tried to be "helpful" by doing a lot of things at once.
  When possible, we should simplify methods to do just one thing, and provide intuitive patterns for doing complex operations using multiple method calls.
  Top-level functions can be used to "synthesize" complex operations, e.g. `pystac.read_file`.

## Key changes

- Rather than making `Collection` a subclass of `Catalog`, both `Catalog` and `Collection` are subclasses of an abstract `Container` class.
- `CatalogType` is deprecated and not used.
  Instead, we provide arguments like `use_absolute_hrefs` and `include_self_href`.
- `StacIO` is deprecated in favor of `Reader` and `Writer`.
  We provide simple wrappers to allow folks to continue using their existing custom `StacIO` classes.
- `Layout` is deprecated in favor of `HrefGenerator`.
  We provide re-implementations of each existing `Layout` (TODO).
- Link hrefs are now more explicit.
  In PySTAC v1, `Link.to_dict()` mutated the `href` based on the `CatalogType` and other factors.
  In PySTAC v2, all href mutation is done _before_ serialization.
