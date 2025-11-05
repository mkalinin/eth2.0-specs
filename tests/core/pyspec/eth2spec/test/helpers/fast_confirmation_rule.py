from eth_utils import encode_hex


def on_slot_after_attestations_applied_and_append_step(spec, store, test_steps):
    spec.on_slot_after_attestations_applied(store)
    test_steps.append({"slot_after_attestations_applied": spec.get_current_slot(store)})
    checks = {
        "time": int(store.time),
        "prev_epoch_unrealized_justified_checkpoint": {
            "epoch": int(store.prev_epoch_unrealized_justified_checkpoint.epoch),
            "root": encode_hex(store.prev_epoch_unrealized_justified_checkpoint.root),
        },
        "prev_slot_head": encode_hex(store.prev_slot_head),
        "confirmed_root": encode_hex(store.confirmed_root),
    }

    test_steps.append({"checks": checks})
