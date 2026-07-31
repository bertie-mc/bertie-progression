package com.berlord.bertie_s1;

import com.mojang.serialization.Codec;
import net.neoforged.neoforge.attachment.AttachmentType;
import net.neoforged.neoforge.registries.DeferredRegister;
import net.neoforged.neoforge.registries.NeoForgeRegistries;

import java.util.function.Supplier;

/** Persistent per-entity flags. */
public final class ModAttachments {
    public static final DeferredRegister<AttachmentType<?>> ATTACHMENTS =
            DeferredRegister.create(NeoForgeRegistries.Keys.ATTACHMENT_TYPES, BertieS1.MODID);

    /**
     * Set once the player consumes a Crafting License. Persists through death and dimension change,
     * so the 3x3 grid is a permanent, earned milestone rather than a place you must return to
     * (replaces the Licensed Crafting Plinth).
     */
    public static final Supplier<AttachmentType<Boolean>> CRAFTING_LICENSED =
            ATTACHMENTS.register("crafting_licensed", () -> AttachmentType
                    .builder(() -> Boolean.FALSE)
                    .serialize(Codec.BOOL)
                    .copyOnDeath()
                    .build());

    /**
     * Ticks until a doomed Allay dies. Set when it first picks up an Arcane Crystal, counted down by
     * {@link AllayCorruptionHandler}. Serialized so the countdown survives a save/quit mid-delay -
     * a 20-50 tick window is short, but an unserialized one would silently cancel the death.
     */
    public static final Supplier<AttachmentType<Integer>> ALLAY_DOOM =
            ATTACHMENTS.register("allay_doom", () -> AttachmentType
                    .builder(() -> 0)
                    .serialize(Codec.INT)
                    .build());

    /** Ticks of lava a Netherly Meal eater must still survive before Fire Resistance lands. */
    public static final Supplier<AttachmentType<Integer>> MEAL_COUNTDOWN =
            ATTACHMENTS.register("meal_countdown", () -> AttachmentType
                    .builder(() -> 0)
                    .serialize(Codec.INT)
                    .build());

    private ModAttachments() {}
}
