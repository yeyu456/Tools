var keywords = ['公寓', '公社', '公舍', '青年社区', '旅社', '旅舍', '酒店', '遇到', '遇道', '遇见', '寓道', 
'豪华', '极客空间', '办公装修', '短租', '经纪人', '经理'];

var site58 = () => {
    let checkBlocks = ['h2 a', '.add', '.jjr_par_dp', '.gongyu'];
    filter('.listUl li', checkBlocks);
};
var siteAnjuke = () => {
    let checkBlocks = ['h3 a', '.details-item'];
    filter('.zu-itemmod', checkBlocks);
};
var siteGanji = () => {
    let checkBlocks = ['.dd-item.title a', '.dd-item.address .area', '.dd-item.source span', '.dd-item.size .last'];
    filter('.f-list-item', checkBlocks);
};

var filter = (nodeSelector, checkBlocks) => {
    let nodes = document.querySelectorAll(nodeSelector);
    nodes.forEach((node) => {
        for (let block of checkBlocks) {
            let dom = node.querySelector(block);
            if (dom && dom.innerText) {
                for (let k of keywords) {
                    if (dom.innerText.indexOf(k) !== -1) {
                        node.remove();
                        break;
                    }
                }    
            }
        }
    });
};
var url = window.location.href;
var mapper = {
    '58.com': site58,
    'anjuke.com': siteAnjuke,
    'ganji.com': siteGanji
};
for (let u of Object.keys(mapper)) {
    if (url.indexOf(u) !== -1) {
        mapper[u]();
        break;
    }
}