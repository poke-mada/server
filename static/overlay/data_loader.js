function doUpdateData(data) {
    const gym1 = document.getElementById('gym1');
    const gym2 = document.getElementById('gym2');
    const gym3 = document.getElementById('gym3');
    const gym4 = document.getElementById('gym4');
    const gym5 = document.getElementById('gym5');
    const gym6 = document.getElementById('gym6');
    const gym7 = document.getElementById('gym7');
    const gym8 = document.getElementById('gym8');

    if (gym1) {
        gym1.classList.remove('d-none')
    }

    if (gym2) {
        gym2.classList.remove('d-none')
    }

    if (gym3) {
        gym3.classList.remove('d-none')
    }

    if (gym4) {
        gym4.classList.remove('d-none')
    }

    if (gym5) {
        gym5.classList.remove('d-none')
    }

    if (gym6) {
        gym6.classList.remove('d-none')
    }

    if (gym7) {
        gym7.classList.remove('d-none')
    }

    if (gym8) {
        gym8.classList.remove('d-none')
    }


    if (!data.gym1) {
        gym1.classList.add('d-none')
    }

    if (!data.gym2) {
        gym2.classList.add('d-none')
    }

    if (!data.gym3) {
        gym3.classList.add('d-none')
    }

    if (!data.gym4) {
        gym4.classList.add('d-none')
    }

    if (!data.gym5) {
        gym5.classList.add('d-none')
    }

    if (!data.gym6) {
        gym6.classList.add('d-none')
    }

    if (!data.gym7) {
        gym7.classList.add('d-none')
    }

    if (!data.gym8) {
        gym8.classList.add('d-none')
    }

    if (!data.team) {
        const pkmnDiv1 = document.getElementById(`pokemon1`);
        const pkmnDiv2 = document.getElementById(`pokemon2`);
        const pkmnDiv3 = document.getElementById(`pokemon3`);
        const pkmnDiv4 = document.getElementById(`pokemon4`);
        const pkmnDiv5 = document.getElementById(`pokemon5`);
        const pkmnDiv6 = document.getElementById(`pokemon6`);

        pkmnDiv1.classList.add('d-none');
        pkmnDiv2.classList.add('d-none');
        pkmnDiv3.classList.add('d-none');
        pkmnDiv4.classList.add('d-none');
        pkmnDiv5.classList.add('d-none');
        pkmnDiv6.classList.add('d-none');
        return;
    }
    data.team = data.team.concat([null,null,null,null,null,null])
    data.team = data.team.slice(0,6)
    data.team.forEach((pokemon, index) => {
        const pkmnDiv = document.getElementById(`pokemon${index + 1}`);
        if (pokemon !== null) {
            pkmnDiv.classList.remove('d-none');
            pkmnDiv.children[0].src = pokemon.sprite_url;
            let moteSpan = pkmnDiv.children[1];
            let x = pokemon.mote.length;
            let fontSize = getSize(x);
            let margins = (31 - fontSize)/2;
            moteSpan.setAttribute('style', `font-size: ${fontSize}px; margin-top: ${margins}px`)
            moteSpan.innerText = pokemon.mote;
        } else {
            pkmnDiv.classList.add('d-none')
        }
    })
}

function getSize(x) {
    const min_value = 12;
    const max_value = 24;
    const min_length = 1;
    const max_length = 13;
    //((-6/12)*(x-1)+18)

    return max_value - ((x - min_length) / (max_length - min_length) * (max_value - min_value))

}

/**
 * @param data
 *
 */
function doUpdateOverlayData(data) {
    setTimeout(() => {
        const overlay = document.getElementById(`alert-overlay`);
        overlay.classList.add('d-none')
    }, 5000)

    const overlay = document.getElementById(`alert-overlay`);
    overlay.classList.remove('d-none')
    const user = document.getElementById(`user`);
    const wildcard = document.getElementById(`wildcard-name`);
    const target = document.getElementById(`target`);

    user.innerText = data.user_name
    wildcard.innerText = data.wildcard.name
    target.innerText = data.target_name
}