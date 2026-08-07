# v0.3.0-rc7
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *

from dataclasses import dataclass


# ---------------------------------------------------------------------------
# ListingGate -- a worked example of consuming OriginalityBond.
#
# A marketplace wants to refuse listings that are unresolved or confirmed
# copies of something already registered. It does not want to build its own
# embeddings pipeline, its own derivation judgment, or its own dispute
# economics -- OriginalityBond already is that primitive.
#
# The interesting part of this example is what it does NOT contain: no
# embeddings, no exec_prompt, no equivalence principle, no vector search. It
# reads one status field. Note also that this contract needs no special
# runner dependency of its own -- it never touches VecDB or SentenceTransformer
# directly, because none of that machinery is its concern.
# ---------------------------------------------------------------------------


ERR_EXPECTED = "EXPECTED"

# Only a live, undisputed claim may back a listing.
LISTABLE_STATUS = 1  # ACTIVE


@gl.contract_interface
class IOriginalityBond:
    class View:
        def get_entry(self, entry_id: u256) -> dict: ...


@allow_storage
@dataclass
class Listing:
    seller: Address
    entry_id: u256
    title: str
    live: bool


class ListingCreated(gl.Event):
    def __init__(self, listing_id: u256, entry_id: u256, /, **blob): ...


class ListingGate(gl.Contract):
    registry: Address
    listings: TreeMap[u256, Listing]
    next_id: u256

    def __init__(self, registry: Address):
        self.registry = registry if isinstance(registry, Address) else Address(registry)
        self.next_id = u256(1)

    @gl.public.write
    def list_item(self, entry_id: u256, title: str) -> u256:
        """List an item backed by an originality claim.

        The entire integration is this one read: only an ACTIVE entry may
        back a listing. PENDING_REVIEW (unresolved), REJECTED (found
        derivative), WITHDRAWN, and CHALLENGE_PENDING (currently disputed)
        are all refused -- a listing must never rest on a claim that is not
        currently a clean, undisputed original.
        """

        entry = IOriginalityBond(self.registry).view().get_entry(entry_id)
        if int(entry["status"]) != LISTABLE_STATUS:
            raise gl.vm.UserError(
                f"{ERR_EXPECTED}: entry {entry_id} is not an active, "
                f"undisputed claim (status={entry['status_name']})"
            )
        if Address(entry["owner"]) != gl.message.sender_address:
            raise gl.vm.UserError(f"{ERR_EXPECTED}: caller does not own that claim")

        listing_id = self.next_id
        self.next_id = u256(int(self.next_id) + 1)

        listing = self.listings.get_or_insert_default(listing_id)
        listing.seller = gl.message.sender_address
        listing.entry_id = entry_id
        listing.title = " ".join(str(title).split())[:160]
        listing.live = True

        ListingCreated(listing_id, entry_id).emit()
        return listing_id

    @gl.public.write
    def delist(self, listing_id: u256) -> None:
        listing = self.listings.get(listing_id)
        if listing is None:
            raise gl.vm.UserError(f"{ERR_EXPECTED}: unknown listing {listing_id}")
        if listing.seller != gl.message.sender_address:
            raise gl.vm.UserError(f"{ERR_EXPECTED}: caller does not own that listing")
        listing.live = False

    @gl.public.view
    def is_still_backed(self, listing_id: u256) -> bool:
        """Re-check the backing claim is still ACTIVE right now.

        A listing's claim can be challenged and lose *after* the listing was
        created -- this view lets a marketplace UI catch that without storing
        any of OriginalityBond's state itself.
        """
        listing = self.listings.get(listing_id)
        if listing is None or not bool(listing.live):
            return False
        entry = IOriginalityBond(self.registry).view().get_entry(listing.entry_id)
        return int(entry["status"]) == LISTABLE_STATUS

    @gl.public.view
    def get_listing(self, listing_id: u256) -> dict:
        listing = self.listings.get(listing_id)
        if listing is None:
            raise gl.vm.UserError(f"{ERR_EXPECTED}: unknown listing {listing_id}")
        return {
            "seller": str(listing.seller),
            "entry_id": int(listing.entry_id),
            "title": str(listing.title),
            "live": bool(listing.live),
        }
