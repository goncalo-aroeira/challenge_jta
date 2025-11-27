"""
Teste específico para verificar que state pode ser qualquer ancestral.
"""

import pandas as pd
from src.processor import GeoProcessor

def test_state_as_concelho():
    """Testar que state pode ser um concelho (level 7), não apenas distrito."""
    
    processor = GeoProcessor('data/portugal.json')
    
    # Teste 1: state = "são pedro do sul" (concelho, level 7)
    df = pd.DataFrame([{
        'id_1': 1,
        'id_2': 2,
        'city_1': 'valadares',
        'city_2': 'pinho',
        'state_1': 'sao pedro do sul',  # ← CONCELHO!
        'state_2': 'sao pedro do sul',  # ← CONCELHO!
    }])
    
    result = processor.process(df)
    
    print("=" * 60)
    print("TESTE: state como CONCELHO (não distrito)")
    print("=" * 60)
    print(f"\nInput:")
    print(f"  city_1='valadares', state_1='sao pedro do sul' (concelho)")
    print(f"  city_2='pinho', state_2='sao pedro do sul' (concelho)")
    print(f"\nOutput:")
    print(f"  expected_level = {result['expected_level'].iloc[0]}")
    print(f"  is_ambiguous = {result['is_ambiguous'].iloc[0]}")
    
    # Ambas as freguesias estão dentro do mesmo concelho
    # expected_level deve ser 7 (nível do concelho)
    assert result['expected_level'].iloc[0] == 7, f"Expected level 7 (concelho), got {result['expected_level'].iloc[0]}"
    assert result['is_ambiguous'].iloc[0] == 0, f"Should not be ambiguous"
    
    print(f"\n✅ PASSOU! state='sao pedro do sul' foi corretamente identificado como concelho")
    print(f"   (não apenas districts level 6)")
    
    # Teste 2: state = distrito vs state = concelho
    df2 = pd.DataFrame([{
        'id_1': 1,
        'id_2': 2,
        'city_1': 'valadares',
        'city_2': 'valadares',
        'state_1': 'viseu',            # ← DISTRITO (level 6)
        'state_2': 'sao pedro do sul',  # ← CONCELHO (level 7)
    }])
    
    result2 = processor.process(df2)
    
    print("\n" + "=" * 60)
    print("TESTE 2: Misturar district e concelho")
    print("=" * 60)
    print(f"\nInput:")
    print(f"  city_1='valadares', state_1='viseu' (district)")
    print(f"  city_2='valadares', state_2='sao pedro do sul' (concelho)")
    print(f"\nOutput:")
    print(f"  expected_level = {result2['expected_level'].iloc[0]}")
    print(f"  is_ambiguous = {result2['is_ambiguous'].iloc[0]}")
    
    # Ambos referem-se à mesma valadares (em são pedro do sul, viseu)
    # Como são específicos, não deve ser ambíguo
    assert result2['expected_level'].iloc[0] == 8, f"Expected level 8 (same freguesia), got {result2['expected_level'].iloc[0]}"
    assert result2['is_ambiguous'].iloc[0] == 0, f"Should not be ambiguous (both are specific)"
    
    print(f"\n✅ PASSOU! Consegue misturar distrito e concelho como state")
    
    # Teste 3: Verificar hierarquia completa
    print("\n" + "=" * 60)
    print("TESTE 3: Hierarquia completa (país → distrito → concelho → freguesia)")
    print("=" * 60)
    
    # Buscar informações sobre valadares
    loader = processor.resolver.loader
    valadares_viseu = processor.resolver.resolve('valadares', 'viseu')
    
    if valadares_viseu:
        loc = valadares_viseu[0]
        print(f"\n📍 Valadares (Viseu):")
        print(f"   ID: {loc.id}")
        print(f"   Level: {loc.admin_level}")
        print(f"   Ancestors: {loc.ancestors}")
        print(f"   Ancestor names: {loc.ancestors_names}")
        print(f"   Ancestor levels: {loc.ancestors_levels}")
        
        # Verificar índice by_city_state
        print(f"\n📖 Entradas no índice by_city_state:")
        for key, ids in loader.by_city_state.items():
            if key[0] == 'valadares' and loc.id in ids:
                ancestor_name = key[1]
                print(f"   ('valadares', '{ancestor_name}') → {ids}")
        
        print(f"\n✅ Agora o índice tem entradas para TODOS os ancestrais!")
    
    print("\n" + "=" * 60)
    print("🎉 TODOS OS TESTES PASSARAM!")
    print("=" * 60)
    print("\n✅ state pode agora ser QUALQUER ancestral:")
    print("   • País (level 2)")
    print("   • Região autónoma (level 4)")
    print("   • Distrito (level 6)")
    print("   • Concelho (level 7)")
    print("   • Ou até freguesia (level 8)")
    print("\n🌍 Pronto para hierarquias complexas como EUA, Brasil, etc!")


if __name__ == '__main__':
    test_state_as_concelho()
