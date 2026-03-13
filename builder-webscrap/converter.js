const fs = require('fs');

const input = JSON.parse(fs.readFileSync('input.json', 'utf8'));
const minecraftItems = JSON.parse(fs.readFileSync('minecraft-items.json', 'utf8'));

const output = [];

for (const y in input) {
  const yLayer = input[y];
  for (const x in yLayer) {
    const xLayer = yLayer[x];
    for (const z in xLayer) {
      const block = xLayer[z];

      const newBlock = {
        coordinates: {
          x: parseInt(x, 10),
          y: parseInt(y, 10),
          z: parseInt(z, 10)
        }
      };

      for (const key in block) {
        if (!['x', 'y', 'z'].includes(key)) {
          newBlock[key] = block[key];
        }
      }

      const sanitizedName = block.name.replace(/\(Bottom\)/g, '').trim();

      newBlock.name = sanitizedName;

      const item = minecraftItems.find(i => i.name === sanitizedName);
      if (item) {
        newBlock.mat_id = item.meta !== 0 ? `${item.type}:${item.meta}` : `${item.type}`;
      }

      output.push({
        ...newBlock.coordinates,
        mat_id: newBlock.mat_id,
        name: newBlock.name,
      });
    }
  }
}

fs.writeFileSync('output.json', JSON.stringify(output, null, 2), 'utf8');

console.log('Conversão concluída! Arquivo salvo como output.json');
