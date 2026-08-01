package com.berlord.bertie_progression.forge;

import net.minecraft.core.component.DataComponentType;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.ItemStack;

import java.util.List;
import java.util.function.Predicate;

/**
 * Data table for the Brick-Forge "bed" interactions (PROGRESSION_SPEC WORLD/SLAG-bed
 * routes that stock stations cannot express). Primary is held in one hand (Opening
 * Mallet in the other); secondary/tertiary are pulled from the player inventory.
 * `sneak` disambiguates same-input pairs (normal vs sneak strike).
 */
public final class BedRecipes {

    public interface StackPredicate extends Predicate<ItemStack> {
        String describe();
    }

    public static StackPredicate item(String id) {
        ResourceLocation rl = ResourceLocation.parse(id);
        return new StackPredicate() {
            @Override public boolean test(ItemStack s) {
                return !s.isEmpty() && BuiltInRegistries.ITEM.getKey(s.getItem()).equals(rl);
            }
            @Override public String describe() { return id; }
        };
    }

    /** Matches a slag:dynamic_part with the given material/part components (slag optional). */
    public static StackPredicate slagPart(String material, String part) {
        return new StackPredicate() {
            @Override public boolean test(ItemStack s) {
                if (s.isEmpty() || !BuiltInRegistries.ITEM.getKey(s.getItem())
                        .equals(ResourceLocation.parse("slag:dynamic_part"))) return false;
                return componentIs(s, "slag:material_type", "slag:" + material)
                        && componentIs(s, "slag:part_type", "slag:" + part);
            }
            @Override public String describe() { return "slag:dynamic_part{" + material + "," + part + "}"; }
        };
    }

    private static boolean componentIs(ItemStack stack, String typeId, String expected) {
        DataComponentType<?> type = BuiltInRegistries.DATA_COMPONENT_TYPE
                .get(ResourceLocation.parse(typeId));
        if (type == null) return false;
        Object val = stack.get(type);
        return val != null && String.valueOf(val).equals(expected);
    }

    public record Input(StackPredicate what, int count) {}

    public record BedRecipe(String id, Input primary, Input secondary, Input tertiary,
                            boolean sneak, String resultId, int resultCount,
                            String extraReturnId, int extraReturnCount) {

        static BedRecipe of(String id, Input primary, Input secondary, Input tertiary,
                            boolean sneak, String resultId, int resultCount) {
            return new BedRecipe(id, primary, secondary, tertiary, sneak, resultId, resultCount, null, 0);
        }
    }

    private static Input in(String id, int count) { return new Input(item(id), count); }

    public static final List<BedRecipe> RECIPES = List.of(
            BedRecipe.of("utrem_jar", in("minecraft:glass", 8),
                    in("forbidden_arcanus:edelwood_planks", 1), null,
                    false, "forbidden_arcanus:utrem_jar", 1)
    );

    public static StackPredicate tag(String tagId) {
        net.minecraft.tags.TagKey<net.minecraft.world.item.Item> key =
                net.minecraft.tags.TagKey.create(net.minecraft.core.registries.Registries.ITEM,
                        ResourceLocation.parse(tagId));
        return new StackPredicate() {
            @Override public boolean test(ItemStack s) { return !s.isEmpty() && s.is(key); }
            @Override public String describe() { return "#" + tagId; }
        };
    }

    private BedRecipes() {}
}
