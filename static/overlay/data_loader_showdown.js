function doUpdateData(data) {

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
    }

    data.team.forEach((pokemon, index) => {
        const pkmnDiv = document.getElementById(`pokemon${index + 1}`);
        if (pokemon !== null) {
            pkmnDiv.classList.remove('d-none');
            pkmnDiv.children[0].src = pokemon.sprite_url;
            let moteSpan = pkmnDiv.children[1];
            let x = pokemon.mote.length;
            let fontSize = getSize(x);
            let margins = (24 - fontSize)/2;
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