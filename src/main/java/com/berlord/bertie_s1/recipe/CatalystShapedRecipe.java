package com.berlord.bertie_s1.recipe;

import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.NonNullList;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.CraftingBookCategory;
import net.minecraft.world.item.crafting.CraftingInput;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.item.crafting.RecipeSerializer;
import net.minecraft.world.item.crafting.ShapedRecipe;
import net.minecraft.world.item.crafting.ShapedRecipePattern;

/**
 * A shaped recipe with a CATALYST ingredient: an input that is matched and required, but returned to
 * the grid instead of being consumed (berlord 2026-07-29, the Gorgon Head in the Sirok's Nest map).
 *
 * <p>This has to be a recipe class rather than data because "is this item consumed" is decided by
 * {@code Recipe.getRemainingItems}, whose vanilla implementation defers to the ITEM's own crafting
 * remainder - which is global to that item in every recipe. A per-recipe catalyst needs the override.
 *
 * <p>{@code getType()} stays {@code minecraft:crafting}, inherited from ShapedRecipe, so this still
 * shows up as an ordinary crafting recipe in EMI and the recipe book and works in any crafter.
 */
public class CatalystShapedRecipe extends ShapedRecipe {

    private final ItemStack output;
    private final Ingredient catalyst;

    public CatalystShapedRecipe(String group, CraftingBookCategory category, ShapedRecipePattern pattern,
                                ItemStack result, boolean showNotification, Ingredient catalyst) {
        super(group, category, pattern, result, showNotification);
        this.output = result;
        this.catalyst = catalyst;
    }

    public Ingredient catalyst() {
        return catalyst;
    }

    @Override
    public NonNullList<ItemStack> getRemainingItems(CraftingInput input) {
        NonNullList<ItemStack> remaining = super.getRemainingItems(input);
        for (int i = 0; i < input.size() && i < remaining.size(); i++) {
            ItemStack in = input.getItem(i);
            if (!in.isEmpty() && catalyst.test(in)) {
                remaining.set(i, in.copyWithCount(1));
            }
        }
        return remaining;
    }

    @Override
    public RecipeSerializer<?> getSerializer() {
        return ModRecipes.CATALYST_SHAPED.get();
    }

    public static class Serializer implements RecipeSerializer<CatalystShapedRecipe> {

        public static final MapCodec<CatalystShapedRecipe> CODEC = RecordCodecBuilder.mapCodec(inst -> inst.group(
                com.mojang.serialization.Codec.STRING.optionalFieldOf("group", "")
                        .forGetter(ShapedRecipe::getGroup),
                CraftingBookCategory.CODEC.optionalFieldOf("category", CraftingBookCategory.MISC)
                        .forGetter(ShapedRecipe::category),
                ShapedRecipePattern.MAP_CODEC.forGetter(r -> r.pattern),
                ItemStack.STRICT_CODEC.fieldOf("result").forGetter(r -> r.output),
                com.mojang.serialization.Codec.BOOL.optionalFieldOf("show_notification", true)
                        .forGetter(ShapedRecipe::showNotification),
                Ingredient.CODEC.fieldOf("catalyst").forGetter(CatalystShapedRecipe::catalyst)
        ).apply(inst, CatalystShapedRecipe::new));

        public static final StreamCodec<RegistryFriendlyByteBuf, CatalystShapedRecipe> STREAM_CODEC =
                StreamCodec.of(Serializer::toNetwork, Serializer::fromNetwork);

        private static void toNetwork(RegistryFriendlyByteBuf buf, CatalystShapedRecipe recipe) {
            buf.writeUtf(recipe.getGroup());
            buf.writeEnum(recipe.category());
            ShapedRecipePattern.STREAM_CODEC.encode(buf, recipe.pattern);
            ItemStack.STREAM_CODEC.encode(buf, recipe.output);
            buf.writeBoolean(recipe.showNotification());
            Ingredient.CONTENTS_STREAM_CODEC.encode(buf, recipe.catalyst);
        }

        private static CatalystShapedRecipe fromNetwork(RegistryFriendlyByteBuf buf) {
            String group = buf.readUtf();
            CraftingBookCategory category = buf.readEnum(CraftingBookCategory.class);
            ShapedRecipePattern pattern = ShapedRecipePattern.STREAM_CODEC.decode(buf);
            ItemStack result = ItemStack.STREAM_CODEC.decode(buf);
            boolean showNotification = buf.readBoolean();
            Ingredient catalyst = Ingredient.CONTENTS_STREAM_CODEC.decode(buf);
            return new CatalystShapedRecipe(group, category, pattern, result, showNotification, catalyst);
        }

        @Override
        public MapCodec<CatalystShapedRecipe> codec() {
            return CODEC;
        }

        @Override
        public StreamCodec<RegistryFriendlyByteBuf, CatalystShapedRecipe> streamCodec() {
            return STREAM_CODEC;
        }
    }
}
