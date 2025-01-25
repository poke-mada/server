import json
import os
import struct
from json import JSONEncoder

TERMINATOR_NULL = 0

BLOCK_SIZE = 56
SLOT_OFFSET = 484
SLOT_DATA_SIZE = (8 + (4 * BLOCK_SIZE))
STAT_DATA_OFFSET = 112
STAT_DATA_SIZE = 22
FORCE_TYPE_ABILITIES = {
    "182": {
        "name": 'Pixilate',
        "forced_from": 'Normal',
        "forced_type": 'Fairy'
    },
    "96": {
        "name": 'Normalize',
        "forced_from": '*',
        "forced_type": 'Normal'
    },
    "184": {
        "name": 'Aerilate',
        "forced_from": 'Normal',
        "forced_type": 'Flying'
    },
    "206": {
        "name": 'Galvanize',
        "forced_from": 'Normal',
        "forced_type": 'Electric'
    },
    "174": {
        "name": 'Refrigerate',
        "forced_from": 'Normal',
        "forced_type": 'Ice'
    }
}


def clean_nick_data(nick_elements):
    result = ''
    for char in nick_elements:
        if char == 0:
            return result
        else:
            result += chr(char)
    return result


def clamp(value, min_value=1, max_value=251):
    if min_value and value < min_value:
        return min_value

    if max_value and value > max_value:
        return max_value

    return value


class PokemonBytes:
    def __init__(self, encrypted_data, *args, **kkwargs):
        super().__init__()
        first_byte = encrypted_data[0]
        if first_byte != 0:
            len_needed = 0
            if len(encrypted_data) < 260:
                encrypted_data_len = len(encrypted_data)
                len_needed = 260 - encrypted_data_len
            self.raw_data = decrypt_data(encrypted_data) + bytes([1] * len_needed)
        else:
            self.raw_data = bytes()

    def species_num(self):
        if len(self.raw_data) > 0:
            return struct.unpack("<H", self.raw_data[0x8:0xA])[0]
        else:
            return 0

    def get_atts(self):
        self.dex_number = self.species_num()
        if self.dex_number == 0:
            return

        self.form = struct.unpack("B", self.raw_data[0x1D:0x1E])[0]
        self.held_item_num = str(struct.unpack("<H", self.raw_data[0xA:0xC])[0])
        self.ability_num = struct.unpack("B", self.raw_data[0x14:0x15])[0]  # Ability
        self.nature_num = struct.unpack("B", self.raw_data[0x1C:0x1D])[0]  ## Nature

        self.level = struct.unpack("B", self.raw_data[0xEC:0xED])[0]  ### Current level
        self.ev_hp = struct.unpack("B", self.raw_data[0x1E:0x1F])[0]
        self.ev_attack = struct.unpack("B", self.raw_data[0x1F:0x20])[0]
        self.ev_defense = struct.unpack("B", self.raw_data[0x20:0x21])[0]
        self.ev_speed = struct.unpack("B", self.raw_data[0x21:0x22])[0]
        self.ev_spatk = struct.unpack("B", self.raw_data[0x22:0x23])[0]
        self.ev_spdef = struct.unpack("B", self.raw_data[0x23:0x24])[0]

        ivloc = struct.unpack("<I", self.raw_data[0x74:0x78])[0]
        self.iv_hp = (ivloc >> 0) & 0x1F  ############################## HP IV
        self.iv_attack = (ivloc >> 5) & 0x1F  ############################## Attack IV
        self.iv_defense = (ivloc >> 10) & 0x1F  ############################# Defense IV
        self.iv_speed = (ivloc >> 15) & 0x1F  ############################# Speed IV
        self.iv_spatk = (ivloc >> 20) & 0x1F  ############################# Special attack IV
        self.iv_spdef = (ivloc >> 25) & 0x1F  ############################# Special defense IV

        mote = struct.unpack("HHHHHHHHHHHHH", self.raw_data[64:90])
        self.mote = clean_nick_data(mote)

        def moves(self):
            move1 = ((0x5A, 0x5C), (0x62, 0x63))
            move2 = ((0x5C, 0x5E), (0x63, 0x64))
            move3 = ((0x5E, 0x60), (0x64, 0x65))
            move4 = ((0x60, 0x62), (0x65, 0x66))
            for ml, pl in (move1, move2, move3, move4):
                move_num = struct.unpack("<H", self.raw_data[ml[0]:ml[1]])[0]
                with open('data/move_data.json') as move_file, open('data/special_move_data.json') as special_move_file:
                    move_data = json.load(move_file)[str(move_num)]
                    special_move_data = json.load(special_move_file)
                    move_type = move_data['typename']

                    if str(move_num) in special_move_data:
                        special_move = special_move_data[str(move_num)]
                        if str(self.held_item_num) in special_move:
                            move_type = special_move[str(self.held_item_num)]

                    if str(self.ability_num) in FORCE_TYPE_ABILITIES:
                        ability_data = FORCE_TYPE_ABILITIES[str(self.ability_num)]
                        if move_type == ability_data['forced_from']:
                            move_type = ability_data['forced_type']
                        elif ability_data['forced_from'] == '*':
                            move_type = ability_data['forced_type']
                    move_data_res = dict(
                        move_name=move_data['movename'],
                        max_pp=move_data['movepp'],
                        type=move_type,
                        power=int(move_data['movepower']),
                        accuracy=int(move_data['moveaccuracy']),
                        category=move_data['movecategoryname']
                    )
                    yield move_num

        self.moves = [move for move in moves(self)]

        with open('data/mon_data.json') as mon_file, open('data/pokemon_forms.json') as forms_file:
            pokemon_data = json.load(mon_file)
            general_forms_data = json.load(forms_file)
            try:
                if str(self.dex_number) in general_forms_data:
                    this_pokemon_data = general_forms_data[str(self.dex_number)]
                    if str(self.form) in this_pokemon_data:
                        pokemon_form_data = this_pokemon_data[str(self.form)]
                    else:
                        pokemon_form_data = this_pokemon_data['0']
                else:
                    pokemon_form_data = pokemon_data[str(self.dex_number)]['0']
            except:
                pokemon_form_data = pokemon_data[str(self.dex_number)]['0']
            try:
                self.species = pokemon_form_data['name']
            except:
                if '0' in pokemon_data[str(self.dex_number)]:
                    species = pokemon_data[str(self.dex_number)]['0']['name']
                    suffix = pokemon_form_data
                    self.species = f'{species} {suffix}'
                    pokemon_form_data = pokemon_data[str(self.dex_number)][suffix]
                else:
                    self.form = pokemon_form_data
                    pokemon_form_data = pokemon_data[str(self.dex_number)][pokemon_form_data]
                    self.species = pokemon_form_data['name']

            self.types = [{'name': value['name'].lower()} for value in pokemon_form_data['types']]

        with open('data/ability_data.json') as ability_file, open('data/nature_data.json') as nature_file, open(
                'data/item_data.json') as item_file:
            ability_data = json.load(ability_file)
            nature_data = json.load(nature_file)
            item_data = json.load(item_file)
            self.ability_name = ability_data[str(self.ability_num)]['name']
            self.nature_name = nature_data[str(self.nature_num)]['name']
            self.item_name = item_data[str(self.held_item_num)]['name']

    def to_dict(self):
        if self.dex_number == 0:
            return None
        return dict(
            level=clamp(self.level),
            dex_number=self.dex_number,
            form=str(self.form),
            held_item=self.held_item_num,
            ability=self.ability_num,
            nature=self.nature_num,
            moves=self.moves,
            mote=self.mote,
            sprite_url=f'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{self.dex_number}.png',
            types=self.types,
            ability_name=self.ability_name,
            nature_name=self.nature_name,
            item_name=self.item_name,
            iv_hp=self.iv_hp,
            iv_attack=self.iv_attack,
            iv_defense=self.iv_defense,
            iv_speed=self.iv_speed,
            iv_spatk=self.iv_spatk,
            iv_spdef=self.iv_spdef,
            ev_hp=self.ev_hp,
            ev_attack=self.ev_attack,
            ev_defense=self.ev_defense,
            ev_speed=self.ev_speed,
            ev_spatk=self.ev_spatk,
            ev_spdef=self.ev_spdef,
        )


def crypt(data, seed, i):
    value = data[i]
    shifted_seed = seed >> 16
    shifted_seed &= 0xFF
    value ^= shifted_seed
    result = struct.pack("B", value)

    value = data[i + 1]
    shifted_seed = seed >> 24
    shifted_seed &= 0xFF
    value ^= shifted_seed
    result += struct.pack("B", value)

    return result


def crypt_array(data, seed, start, end):
    result = bytes()
    temp_seed = seed

    for i in range(start, end, 2):
        temp_seed *= 0x41C64E6D
        temp_seed &= 0xFFFFFFFF
        temp_seed += 0x00006073
        temp_seed &= 0xFFFFFFFF
        result += crypt(data, temp_seed, i)

    return result


def shuffle_array(data, sv, block_size):
    block_position = [[0, 0, 0, 0, 0, 0, 1, 1, 2, 3, 2, 3, 1, 1, 2, 3, 2, 3, 1, 1, 2, 3, 2, 3],
                      [1, 1, 2, 3, 2, 3, 0, 0, 0, 0, 0, 0, 2, 3, 1, 1, 3, 2, 2, 3, 1, 1, 3, 2],
                      [2, 3, 1, 1, 3, 2, 2, 3, 1, 1, 3, 2, 0, 0, 0, 0, 0, 0, 3, 2, 3, 2, 1, 1],
                      [3, 2, 3, 2, 1, 1, 3, 2, 3, 2, 1, 1, 3, 2, 3, 2, 1, 1, 0, 0, 0, 0, 0, 0]]
    result = bytes()
    for block in range(4):
        start = block_size * block_position[block][sv]
        end = start + block_size
        result += data[start:end]
    return result


def decrypt_data(encrypted_data):
    pv = struct.unpack("<I", encrypted_data[:4])[0]
    sv = ((pv >> 13) & 31) % 24

    start = 8
    end = (4 * BLOCK_SIZE) + 8

    header = encrypted_data[:8]

    # Blocks
    blocks = crypt_array(encrypted_data, pv, start, end)

    # Stats
    stats = crypt_array(encrypted_data, pv, end, len(encrypted_data))

    final_result = header + shuffle_array(blocks, sv, BLOCK_SIZE) + stats

    return final_result


def normalize_gender_symbol(char):
    # Aquí iría la lógica para normalizar el carácter
    match char:
        case '\uE08E':
            return '\u2642'
        case '\uE08F':
            return '\u2640'
    return char


def get_string(data):
    result = []
    length = load_string(data, result)
    return ''.join(result[:length])  # Crear una cadena con los caracteres procesados


def load_string(data, result):
    ctr = 0
    i = 0
    while i < len(data):
        # Leer 2 bytes (como en ReadUInt16LittleEndian)
        value = struct.unpack('<H', data[i:i + 2])[0]  # '<H' es para little-endian, unsigned short
        if value == TERMINATOR_NULL:
            break
        result.append(normalize_gender_symbol(chr(value)))
        i += 2
        ctr += 1
    return ctr


def get_party_slot(data):
    pokemon_data_size = 0x104
    return data[:pokemon_data_size]


def get_party_offset(slot):
    party_memory_address = 0x14200
    pokemon_data_size = 0x104
    return party_memory_address + (pokemon_data_size * slot)


def get_party_span(data, slot):
    return data[get_party_offset(slot):]


def get_pokemon_in_slot(data, slot):
    return get_party_slot(get_party_span(data, slot))


def get_box_offset(box):
    box_address = 0x22600
    SIZE_6STORED = 232
    return box_address + (SIZE_6STORED * box * 30)


def get_box_slot_offset(box, slot):
    SIZE_6STORED = 232
    return get_box_offset(box) + (slot * SIZE_6STORED)


def get_stored_slot(data):
    SIZE_6STORED = 232
    pokemon_data = data[:SIZE_6STORED]
    stat_data = bytes()
    data = pokemon_data + stat_data
    pokemon = PokemonBytes(data, True)
    pokemon.get_atts()
    return pokemon.to_dict()


def get_box_slot(data, box_slot_offset):
    return get_stored_slot(data[box_slot_offset:])


def get_pokemon_at_box_slot(data, box, slot):
    return get_box_slot(data, get_box_slot_offset(box, slot))


def get_trainer_name(save_data):
    offset = 0x14000
    length = 0x00170

    trainer_memory_block = save_data[offset: offset + length]
    original_thrash_nick = trainer_memory_block[0x48:0x48 + 0x1A]
    trainer_name = get_string(original_thrash_nick)
    return trainer_name


def data_reader(save_data):
    offset = 0x14000
    length = 0x00170

    trainer_memory_block = save_data[offset: offset + length]
    original_thrash_nick = trainer_memory_block[0x48:0x48 + 0x1A]
    trainer_team = []
    total_boxes = range(31)
    boxes = dict()

    trainer_name = get_string(original_thrash_nick)

    for slot in range(6):
        pokemon = PokemonBytes(get_pokemon_in_slot(save_data, slot))
        pokemon.get_atts()
        trainer_team.append(pokemon.to_dict())

    for box in total_boxes:
        box_list = []
        for slot in range(30):
            pokemon = get_pokemon_at_box_slot(save_data, box, slot)
            if pokemon:
                box_list.append(dict(
                    slot=slot,
                    pokemon=pokemon
                ))

        if len(box_list) > 0:
            boxes[box] = box_list

    return dict(
        boxes=boxes,
        trainer_name=trainer_name,
        team=trainer_team
    )
