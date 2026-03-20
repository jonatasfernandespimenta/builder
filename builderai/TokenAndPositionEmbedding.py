from tensorflow.keras import layers, models, losses, callbacks
import tensorflow as tf
import keras


@keras.saving.register_keras_serializable()
class TokenAndPositionEmbedding(layers.Layer):
    def __init__(self, max_len, vocab_size, embed_dim, max_coord=128, **kwargs):
        super(TokenAndPositionEmbedding, self).__init__(**kwargs)
        self.max_len = max_len
        self.vocab_size = vocab_size
        self.embed_dim = embed_dim
        self.max_coord = max_coord
        self.token_emb = layers.Embedding(input_dim=vocab_size, output_dim=embed_dim)
        self.pos_emb = layers.Embedding(input_dim=max_len, output_dim=embed_dim)
        # Learned embeddings for each spatial axis
        self.x_emb = layers.Embedding(input_dim=max_coord, output_dim=embed_dim)
        self.y_emb = layers.Embedding(input_dim=max_coord, output_dim=embed_dim)
        self.z_emb = layers.Embedding(input_dim=max_coord, output_dim=embed_dim)

    def build(self, input_shape):
        self.token_emb.build(input_shape)
        self.pos_emb.build(input_shape)
        self.x_emb.build(input_shape)
        self.y_emb.build(input_shape)
        self.z_emb.build(input_shape)
        super().build(input_shape)

    def call(self, x, spatial_coords=None):
        """
        Args:
            x: token ids, shape (batch, seq_len)
            spatial_coords: optional (batch, seq_len, 3) tensor of [x,y,z] coords.
                           Non-block tokens should have coords [0,0,0].
                           When None, falls back to sequential positional encoding only.
        """
        maxlen = tf.shape(x)[-1]
        positions = tf.range(start=0, limit=maxlen, delta=1)
        token_embeddings = self.token_emb(x)
        pos_embeddings = self.pos_emb(positions)

        output = token_embeddings + pos_embeddings

        if spatial_coords is not None:
            # spatial_coords shape: (batch, seq_len, 3)
            x_coords = tf.clip_by_value(spatial_coords[:, :, 0], 0, self.max_coord - 1)
            y_coords = tf.clip_by_value(spatial_coords[:, :, 1], 0, self.max_coord - 1)
            z_coords = tf.clip_by_value(spatial_coords[:, :, 2], 0, self.max_coord - 1)

            spatial = self.x_emb(x_coords) + self.y_emb(y_coords) + self.z_emb(z_coords)
            output = output + spatial

        return output

    def get_config(self):
        config = super().get_config()
        config.update(
            {
                "max_len": self.max_len,
                "vocab_size": self.vocab_size,
                "embed_dim": self.embed_dim,
                "max_coord": self.max_coord,
            }
        )
        return config
    